"""Utilities for function refactoring and code organization."""

from typing import Dict, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def extract_validation_logic(validation_func: Callable):
    """Decorator to extract validation logic from main functions."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Run validation first
            validation_result = validation_func(*args, **kwargs)
            if validation_result is not True:
                return validation_result
            # Run main function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def extract_data_processing(processing_func: Callable):
    """Decorator to extract data processing logic."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Process data first
            processed_args, processed_kwargs = processing_func(*args, **kwargs)
            # Run main function with processed data
            return func(*processed_args, **processed_kwargs)

        return wrapper

    return decorator


class FunctionBreaker:
    """Helper class to break down large functions into smaller components."""

    @staticmethod
    def extract_error_handling(main_func: Callable, error_handler: Callable):
        """Extract error handling from main function."""

        @wraps(main_func)
        def wrapper(*args, **kwargs):
            try:
                return main_func(*args, **kwargs)
            except Exception as e:
                return error_handler(e, *args, **kwargs)

        return wrapper

    @staticmethod
    def extract_response_formatting(main_func: Callable, formatter: Callable):
        """Extract response formatting from main function."""

        @wraps(main_func)
        def wrapper(*args, **kwargs):
            result = main_func(*args, **kwargs)
            return formatter(result)

        return wrapper

    @staticmethod
    def create_pipeline(*functions):
        """Create a pipeline of functions."""

        def pipeline(data):
            for func in functions:
                data = func(data)
            return data

        return pipeline


def split_function_by_concerns(func_dict: Dict[str, Callable]) -> Callable:
    """Split function into multiple concerns and combine them."""

    def combined_function(*args, **kwargs):
        context = {"args": args, "kwargs": kwargs}

        # Execute functions in order
        for name, func in func_dict.items():
            try:
                result = func(context)
                if name == "main":
                    return result
                context[name] = result
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                raise

        return context.get("main")

    return combined_function
