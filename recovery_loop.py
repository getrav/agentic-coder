import time
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging


class RecoveryStrategy(Enum):
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    ALTERNATIVE_AGENT = "alternative_agent"
    FALLBACK_DEFAULT = "fallback_default"


@dataclass
class RecoveryAttempt:
    attempt_number: int
    timestamp: datetime
    error: str
    strategy_used: RecoveryStrategy
    success: bool = False
    duration_ms: float = 0.0


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    circuit_open: bool = False
    reset_timeout_seconds: int = 60
    
    def should_allow_request(self) -> bool:
        if not self.circuit_open:
            return True
        
        if self.last_failure_time:
            time_since_failure = datetime.now() - self.last_failure_time
            if time_since_failure.total_seconds() > self.reset_timeout_seconds:
                self.circuit_open = False
                self.failure_count = 0
                return True
        
        return False
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= 3:  # Open circuit after 3 failures
            self.circuit_open = True


class RecoveryLoop:
    def __init__(self, 
                 max_retries: int = 3,
                 default_strategy: RecoveryStrategy = RecoveryStrategy.EXPONENTIAL_BACKOFF,
                 base_delay_ms: int = 1000,
                 max_delay_ms: int = 30000,
                 circuit_breaker_threshold: int = 3,
                 enable_logging: bool = True):
        self.max_retries = max_retries
        self.default_strategy = default_strategy
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.enable_logging = enable_logging
        
        self.recovery_history: List[RecoveryAttempt] = []
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        
        self.logger = logging.getLogger(__name__)
        
    def register_circuit_breaker(self, agent_name: str, reset_timeout_seconds: int = 60):
        """Register a circuit breaker for a specific agent"""
        self.circuit_breakers[agent_name] = CircuitBreakerState(
            reset_timeout_seconds=reset_timeout_seconds
        )
    
    def _can_execute_agent(self, agent_name: str) -> bool:
        """Check if agent can be executed (circuit breaker logic)"""
        if agent_name not in self.circuit_breakers:
            return True
        
        return self.circuit_breakers[agent_name].should_allow_request()
    
    def _record_failure(self, agent_name: str, error: str):
        """Record a failure for circuit breaker"""
        if agent_name in self.circuit_breakers:
            self.circuit_breakers[agent_name].record_failure()
    
    def _get_delay_ms(self, attempt: int, strategy: RecoveryStrategy) -> float:
        """Calculate delay based on strategy and attempt number"""
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return 0
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay_ms * (2 ** (attempt - 1))
            return min(delay, self.max_delay_ms)
        else:
            return 0
    
    def _log_recovery_attempt(self, attempt: RecoveryAttempt):
        """Log recovery attempt details"""
        if self.enable_logging:
            status = "✅" if attempt.success else "❌"
            self.logger.info(
                f"{status} Recovery Attempt #{attempt.attempt_number} | "
                f"Strategy: {attempt.strategy_used.value} | "
                f"Duration: {attempt.duration_ms:.2f}ms | "
                f"Success: {attempt.success}"
            )
            if not attempt.success:
                self.logger.warning(f"Error: {attempt.error}")
    
    async def execute_with_recovery(self,
                                  agent_name: str,
                                  agent_func: Callable,
                                  input_data: Dict[str, Any],
                                  strategies: Optional[List[RecoveryStrategy]] = None,
                                  alternative_agents: Optional[Dict[str, Callable]] = None,
                                  fallback_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an agent with recovery logic
        
        Args:
            agent_name: Name of the primary agent
            agent_func: Agent function to execute
            input_data: Input data for the agent
            strategies: List of recovery strategies to try (in order)
            alternative_agents: Dictionary of alternative agent functions
            fallback_result: Default result if all recovery attempts fail
        """
        if strategies is None:
            strategies = [self.default_strategy]
        
        if alternative_agents is None:
            alternative_agents = {}
        
        # Check circuit breaker
        if not self._can_execute_agent(agent_name):
            error_msg = f"Circuit breaker open for agent: {agent_name}"
            self._record_failure(agent_name, error_msg)
            
            # Try alternative agents
            if RecoveryStrategy.ALTERNATIVE_AGENT in strategies:
                alt_agent_name = f"{agent_name}_fallback"
                if alt_agent_name in alternative_agents:
                    return await self.execute_with_recovery(
                        alt_agent_name,
                        alternative_agents[alt_agent_name],
                        input_data,
                        [s for s in strategies if s != RecoveryStrategy.ALTERNATIVE_AGENT],
                        alternative_agents,
                        fallback_result
                    )
            
            # Use fallback if available
            if fallback_result is not None:
                return {
                    "agent": agent_name,
                    "result": fallback_result,
                    "status": "fallback",
                    "error": error_msg,
                    "recovery_applied": True
                }
            
            return {
                "agent": agent_name,
                "error": error_msg,
                "status": "failed",
                "recovery_applied": True,
                "circuit_breaker_triggered": True
            }
        
        # Try execution with recovery
        last_error = None
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            strategy = strategies[attempt % len(strategies)] if attempt > 0 else strategies[0]
            
            # Calculate delay for retries
            if attempt > 0:
                delay_ms = self._get_delay_ms(attempt, strategy)
                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000.0)
            
            start_time = time.time()
            attempt_record = RecoveryAttempt(
                attempt_number=attempt + 1,
                timestamp=datetime.now(),
                error="",
                strategy_used=strategy
            )
            
            try:
                # Execute agent
                if asyncio.iscoroutinefunction(agent_func):
                    result = await agent_func(input_data)
                else:
                    result = agent_func(input_data)
                
                # Success
                attempt_record.success = True
                attempt_record.duration_ms = (time.time() - start_time) * 1000
                self._log_recovery_attempt(attempt_record)
                self.recovery_history.append(attempt_record)
                
                return {
                    "agent": agent_name,
                    "result": result,
                    "status": "success",
                    "recovery_attempts": attempt if attempt > 0 else 0,
                    "recovery_applied": attempt > 0
                }
                
            except Exception as e:
                # Failure
                error_msg = str(e)
                last_error = error_msg
                attempt_record.error = error_msg
                attempt_record.duration_ms = (time.time() - start_time) * 1000
                self._log_recovery_attempt(attempt_record)
                self.recovery_history.append(attempt_record)
                
                # Record failure for circuit breaker
                self._record_failure(agent_name, error_msg)
                
                # If this is the last attempt, try alternative agents or fallback
                if attempt == self.max_retries:
                    if RecoveryStrategy.ALTERNATIVE_AGENT in strategies:
                        alt_agent_name = f"{agent_name}_fallback"
                        if alt_agent_name in alternative_agents:
                            return await self.execute_with_recovery(
                                alt_agent_name,
                                alternative_agents[alt_agent_name],
                                input_data,
                                [s for s in strategies if s != RecoveryStrategy.ALTERNATIVE_AGENT],
                                alternative_agents,
                                fallback_result
                            )
                    
                    if RecoveryStrategy.FALLBACK_DEFAULT in strategies and fallback_result is not None:
                        return {
                            "agent": agent_name,
                            "result": fallback_result,
                            "status": "fallback",
                            "error": last_error,
                            "recovery_applied": True,
                            "recovery_attempts": attempt + 1
                        }
                    
                    # All recovery attempts failed
                    return {
                        "agent": agent_name,
                        "error": last_error,
                        "status": "failed",
                        "recovery_applied": True,
                        "recovery_attempts": attempt + 1,
                        "circuit_breaker_triggered": self.circuit_breakers[agent_name].circuit_open if agent_name in self.circuit_breakers else False
                    }
                
                # Continue to next retry
                continue
        
        # This should never be reached due to the loop logic, but add a fallback return
        return {
            "agent": agent_name,
            "error": "Unexpected error in recovery loop",
            "status": "failed",
            "recovery_applied": False
        }
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get statistics about recovery attempts"""
        if not self.recovery_history:
            return {"total_attempts": 0}
        
        successful_attempts = [a for a in self.recovery_history if a.success]
        failed_attempts = [a for a in self.recovery_history if not a.success]
        
        strategy_counts = {}
        for attempt in self.recovery_history:
            strategy = attempt.strategy_used.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            "total_attempts": len(self.recovery_history),
            "successful_attempts": len(successful_attempts),
            "failed_attempts": len(failed_attempts),
            "success_rate": len(successful_attempts) / len(self.recovery_history) if self.recovery_history else 0,
            "average_duration_ms": sum(a.duration_ms for a in self.recovery_history) / len(self.recovery_history) if self.recovery_history else 0,
            "strategies_used": strategy_counts,
            "circuit_breakers": {
                name: {
                    "circuit_open": state.circuit_open,
                    "failure_count": state.failure_count,
                    "last_failure": state.last_failure_time.isoformat() if state.last_failure_time else None
                }
                for name, state in self.circuit_breakers.items()
            }
        }
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        for cb_state in self.circuit_breakers.values():
            cb_state.circuit_open = False
            cb_state.failure_count = 0
            cb_state.last_failure_time = None
    
    def clear_recovery_history(self):
        """Clear recovery attempt history"""
        self.recovery_history.clear()