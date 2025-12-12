priority': 'u=4'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416166.6245592}
2025-12-11 02:22:46,628 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/countries/', 'path': '/api/countries/', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': '*/*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/dashboard', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=4'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416166.6287518}
2025-12-11 02:22:46,632 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/verification/textverified/services', 'path': '/api/verification/textverified/services', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': '*/*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/dashboard', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=4'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416166.632805}
2025-12-11 02:22:46,635 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/dashboard/activity/recent', 'path': '/api/dashboard/activity/recent', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': '*/*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/dashboard', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=4'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416166.635745}
2025-12-11 02:22:46,683 - app.api.verification.textverified_endpoints - INFO - Balance endpoint called
2025-12-11 02:22:46,683 - app.services.textverified_service - INFO - TextVerified service initialization attempt
2025-12-11 02:22:46,685 - app.services.textverified_service - INFO - TextVerified credentials validated successfully
2025-12-11 02:22:46,686 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-12-11 02:22:48,290 - app.services.textverified_service - INFO - Balance retrieved: 18.75 USD
2025-12-11 02:22:48,290 - app.api.verification.textverified_endpoints - INFO - Balance retrieved: 18.75 USD
2025-12-11 02:22:49,468 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/verification/textverified/balance', 'status_code': 200, 'process_time': 2.848, 'user_id': None, 'timestamp': 1765416169.468819}
INFO:     127.0.0.1:58707 - "GET /api/verification/textverified/balance HTTP/1.1" 200 OK
2025-12-11 02:22:49,472 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/countries/', 'status_code': 200, 'process_time': 2.843, 'user_id': None, 'timestamp': 1765416169.47214}
INFO:     127.0.0.1:58709 - "GET /api/countries/ HTTP/1.1" 200 OK
2025-12-11 02:22:49,483 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/notifications', 'path': '/api/notifications', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': '*/*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/dashboard', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=4'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416169.4832451}
2025-12-11 02:22:49,485 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/admin/balance-test', 'path': '/api/admin/balance-test', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': '*/*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/dashboard', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=4'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416169.485441}
2025-12-11 02:22:49,487 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/user/profile', 'status_code': 200, 'process_time': 2.887, 'user_id': None, 'timestamp': 1765416169.487662}
INFO:     127.0.0.1:58704 - "GET /api/user/profile HTTP/1.1" 200 OK
2025-12-11 02:22:49,489 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/verification/textverified/services', 'status_code': 200, 'process_time': 2.857, 'user_id': None, 'timestamp': 1765416169.489781}
INFO:     127.0.0.1:58710 - "GET /api/verification/textverified/services HTTP/1.1" 200 OK
2025-12-11 02:22:49,491 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/analytics/summary', 'status_code': 200, 'process_time': 2.867, 'user_id': None, 'timestamp': 1765416169.491054}
INFO:     127.0.0.1:58708 - "GET /api/analytics/summary HTTP/1.1" 200 OK
2025-12-11 02:22:49,499 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/dashboard/activity/recent', 'status_code': 200, 'process_time': 2.863, 'user_id': None, 'timestamp': 1765416169.49913}
INFO:     127.0.0.1:58711 - "GET /api/dashboard/activity/recent HTTP/1.1" 200 OK
2025-12-11 02:22:49,512 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/notifications', 'status_code': 200, 'process_time': 0.03, 'user_id': None, 'timestamp': 1765416169.512929}
INFO:     127.0.0.1:58707 - "GET /api/notifications HTTP/1.1" 200 OK
2025-12-11 02:22:49,947 - app.services.textverified_api - INFO - TextVerified balance fetched: $18.75
2025-12-11 02:22:49,950 - balance_test - ERROR - TextVerified balance test failed: AttributeError: 'float' object has no attribute 'get'
2025-12-11 02:22:49,956 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/admin/balance-test', 'status_code': 200, 'process_time': 0.471, 'user_id': None, 'timestamp': 1765416169.956716}
INFO:     127.0.0.1:58709 - "GET /api/admin/balance-test HTTP/1.1" 200 OK
2025-12-11 02:23:13,998 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/verify', 'path': '/verify', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/dashboard', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'upgrade-insecure-requests': '1', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin', 'sec-fetch-user': '?1', 'priority': 'u=0, i'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416193.998327}
2025-12-11 02:23:14,045 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/verify', 'status_code': 200, 'process_time': 0.048, 'user_id': None, 'timestamp': 1765416194.0458019}
INFO:     127.0.0.1:58722 - "GET /verify HTTP/1.1" 200 OK
2025-12-11 02:23:14,154 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/verification/textverified/balance', 'path': '/api/verification/textverified/balance', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'application/json, text/plain, */*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/verify', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416194.1543949}
2025-12-11 02:23:14,156 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'http://127.0.0.1:8000/api/verification/textverified/services', 'path': '/api/verification/textverified/services', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'application/json, text/plain, */*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/verify', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416194.155993}
2025-12-11 02:23:14,165 - app.api.verification.textverified_endpoints - INFO - Balance endpoint called
2025-12-11 02:23:14,165 - app.services.textverified_service - INFO - TextVerified service initialization attempt
2025-12-11 02:23:14,165 - app.services.textverified_service - INFO - TextVerified credentials validated successfully
2025-12-11 02:23:14,166 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-12-11 02:23:15,817 - app.services.textverified_service - INFO - Balance retrieved: 18.75 USD
2025-12-11 02:23:15,818 - app.api.verification.textverified_endpoints - INFO - Balance retrieved: 18.75 USD
2025-12-11 02:23:17,263 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/verification/textverified/balance', 'status_code': 200, 'process_time': 3.109, 'user_id': None, 'timestamp': 1765416197.263456}
INFO:     127.0.0.1:58722 - "GET /api/verification/textverified/balance HTTP/1.1" 200 OK
2025-12-11 02:23:17,268 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/api/verification/textverified/services', 'status_code': 200, 'process_time': 3.113, 'user_id': None, 'timestamp': 1765416197.268503}
INFO:     127.0.0.1:58723 - "GET /api/verification/textverified/services HTTP/1.1" 200 OK
2025-12-11 02:23:46,602 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'POST', 'url': 'http://127.0.0.1:8000/api/verify/create', 'path': '/api/verify/create', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'application/json, text/plain, */*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/verify', 'content-type': 'application/json', 'content-length': '60', 'origin': 'http://127.0.0.1:8000', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=0'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416226.602547}
2025-12-11 02:23:46,624 - app.services.textverified_service - INFO - TextVerified service initialization attempt
2025-12-11 02:23:46,625 - app.services.textverified_service - INFO - TextVerified credentials validated successfully
2025-12-11 02:23:46,626 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-12-11 02:23:46,627 - app.services.textverified_service - INFO - Purchasing number for ourtime in US
2025-12-11 02:23:48,879 - app.services.textverified_service - INFO - Number purchased: lr_01KC5G3NRXKPWJCGNE298YENGM
2025-12-11 02:23:48,895 - app.api.verification.consolidated_verification - INFO - Verification created: 2e565467-d8e6-41bd-b446-ab2bf3c19f0c
2025-12-11 02:23:48,954 - app.services.sms_polling_service - INFO - Started polling for verification 2e565467-d8e6-41bd-b446-ab2bf3c19f0c
2025-12-11 02:23:50,715 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:23:50,716 - app.core.unified_error_handling - ERROR - Unhandled error in POST http://127.0.0.1:8000/api/verify/create: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}
Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 157, in call_next
    message = await recv_stream.receive()
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/anyio/streams/memory.py", line 126, in receive
    raise EndOfStream from None
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_error_handling.py", line 125, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 189, in __call__
    response_sent.set()
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/contextlib.py", line 135, in __exit__
    self.gen.throw(type, value, traceback)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_utils.py", line 82, in collapse_excgroups
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 187, in __call__
    response = await self.dispatch_func(request, call_next)
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_rate_limiting.py", line 363, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 93, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 20, in __call__
    await responder(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 39, in __call__
    await self.app(scope, receive, self.send_with_gzip)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 715, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 735, in app
    await route.handle(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 288, in handle
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 119, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 105, in app
    response = await f(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 407, in app
    content = await serialize_response(
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 248, in serialize_response
    raise ResponseValidationError(
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}

2025-12-11 02:23:50,775 - middleware.logging - ERROR - HTTP response - server error: {'event': 'response', 'method': 'POST', 'path': '/api/verify/create', 'status_code': 500, 'process_time': 4.173, 'user_id': None, 'timestamp': 1765416230.7755032}
INFO:     127.0.0.1:58732 - "POST /api/verify/create HTTP/1.1" 500 Internal Server Error
2025-12-11 02:23:52,100 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:23:54,460 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:23:58,831 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:23:58,832 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:04,495 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:05,876 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:08,233 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:09,143 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'POST', 'url': 'http://127.0.0.1:8000/api/verify/create', 'path': '/api/verify/create', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'application/json, text/plain, */*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/verify', 'content-type': 'application/json', 'content-length': '65', 'origin': 'http://127.0.0.1:8000', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=0'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416249.1435819}
2025-12-11 02:24:09,155 - app.services.textverified_service - INFO - TextVerified service initialization attempt
2025-12-11 02:24:09,156 - app.services.textverified_service - INFO - TextVerified credentials validated successfully
2025-12-11 02:24:09,156 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-12-11 02:24:09,156 - app.services.textverified_service - INFO - Purchasing number for plentyoffish in US
2025-12-11 02:24:12,484 - app.services.textverified_service - INFO - Number purchased: lr_01KC5G4BYER1E5W68AZYAJKAWB
2025-12-11 02:24:12,490 - app.api.verification.consolidated_verification - INFO - Verification created: 559de670-dafd-4ea8-a251-48148bca393c
2025-12-11 02:24:12,866 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:12,867 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:12,868 - app.core.unified_error_handling - ERROR - Unhandled error in POST http://127.0.0.1:8000/api/verify/create: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}
Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 157, in call_next
    message = await recv_stream.receive()
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/anyio/streams/memory.py", line 126, in receive
    raise EndOfStream from None
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_error_handling.py", line 125, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 189, in __call__
    response_sent.set()
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/contextlib.py", line 135, in __exit__
    self.gen.throw(type, value, traceback)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_utils.py", line 82, in collapse_excgroups
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 187, in __call__
    response = await self.dispatch_func(request, call_next)
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_rate_limiting.py", line 363, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 93, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 20, in __call__
    await responder(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 39, in __call__
    await self.app(scope, receive, self.send_with_gzip)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 715, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 735, in app
    await route.handle(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 288, in handle
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 119, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 105, in app
    response = await f(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 407, in app
    content = await serialize_response(
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 248, in serialize_response
    raise ResponseValidationError(
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}

2025-12-11 02:24:12,870 - middleware.logging - ERROR - HTTP response - server error: {'event': 'response', 'method': 'POST', 'path': '/api/verify/create', 'status_code': 500, 'process_time': 3.727, 'user_id': None, 'timestamp': 1765416252.870674}
INFO:     127.0.0.1:58737 - "POST /api/verify/create HTTP/1.1" 500 Internal Server Error
2025-12-11 02:24:18,216 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:18,959 - app.services.sms_polling_service - INFO - Started polling for verification 559de670-dafd-4ea8-a251-48148bca393c
2025-12-11 02:24:19,346 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:19,700 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:20,702 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:22,106 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:23,131 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:24,646 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'POST', 'url': 'http://127.0.0.1:8000/api/verify/create', 'path': '/api/verify/create', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'application/json, text/plain, */*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/verify', 'content-type': 'application/json', 'content-length': '65', 'origin': 'http://127.0.0.1:8000', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=0'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416264.64655}
2025-12-11 02:24:24,660 - app.services.textverified_service - INFO - TextVerified service initialization attempt
2025-12-11 02:24:24,660 - app.services.textverified_service - INFO - TextVerified credentials validated successfully
2025-12-11 02:24:24,661 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-12-11 02:24:24,661 - app.services.textverified_service - INFO - Purchasing number for plentyoffish in US
2025-12-11 02:24:27,524 - app.services.textverified_service - INFO - Number purchased: lr_01KC5G4V2RHD28PEZM727Z2DVR
2025-12-11 02:24:27,536 - app.api.verification.consolidated_verification - INFO - Verification created: 7ca0a1c7-f050-403c-bc90-c788aeb6f62d
2025-12-11 02:24:27,907 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:27,908 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:28,272 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:28,272 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:28,273 - app.core.unified_error_handling - ERROR - Unhandled error in POST http://127.0.0.1:8000/api/verify/create: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}
Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 157, in call_next
    message = await recv_stream.receive()
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/anyio/streams/memory.py", line 126, in receive
    raise EndOfStream from None
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_error_handling.py", line 125, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 189, in __call__
    response_sent.set()
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/contextlib.py", line 135, in __exit__
    self.gen.throw(type, value, traceback)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_utils.py", line 82, in collapse_excgroups
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 187, in __call__
    response = await self.dispatch_func(request, call_next)
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_rate_limiting.py", line 363, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 93, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 20, in __call__
    await responder(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 39, in __call__
    await self.app(scope, receive, self.send_with_gzip)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 715, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 735, in app
    await route.handle(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 288, in handle
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 119, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 105, in app
    response = await f(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 407, in app
    content = await serialize_response(
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 248, in serialize_response
    raise ResponseValidationError(
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}

2025-12-11 02:24:28,288 - middleware.logging - ERROR - HTTP response - server error: {'event': 'response', 'method': 'POST', 'path': '/api/verify/create', 'status_code': 500, 'process_time': 3.632, 'user_id': None, 'timestamp': 1765416268.287322}
INFO:     127.0.0.1:58743 - "POST /api/verify/create HTTP/1.1" 500 Internal Server Error
2025-12-11 02:24:33,255 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:33,624 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:33,625 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'POST', 'url': 'http://127.0.0.1:8000/api/verify/create', 'path': '/api/verify/create', 'query_params': {}, 'headers': {'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0', 'accept': 'application/json, text/plain, */*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br, zstd', 'referer': 'http://127.0.0.1:8000/verify', 'content-type': 'application/json', 'content-length': '65', 'origin': 'http://127.0.0.1:8000', 'sec-gpc': '1', 'connection': 'keep-alive', 'cookie': '[REDACTED]', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'priority': 'u=0'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1765416273.625657}
2025-12-11 02:24:33,640 - app.services.textverified_service - INFO - TextVerified service initialization attempt
2025-12-11 02:24:33,641 - app.services.textverified_service - INFO - TextVerified credentials validated successfully
2025-12-11 02:24:33,641 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-12-11 02:24:33,641 - app.services.textverified_service - INFO - Purchasing number for plentyoffish in US
2025-12-11 02:24:35,976 - app.services.textverified_service - INFO - Number purchased: lr_01KC5G53R088ZCVJVNE6G8D4NH
2025-12-11 02:24:35,986 - app.api.verification.consolidated_verification - INFO - Verification created: 50729c4f-1299-41e7-9598-23b2d9af32c6
2025-12-11 02:24:36,339 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:36,714 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:36,716 - app.core.unified_error_handling - ERROR - Unhandled error in POST http://127.0.0.1:8000/api/verify/create: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}
Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 157, in call_next
    message = await recv_stream.receive()
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/anyio/streams/memory.py", line 126, in receive
    raise EndOfStream from None
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_error_handling.py", line 125, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 189, in __call__
    response_sent.set()
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/contextlib.py", line 135, in __exit__
    self.gen.throw(type, value, traceback)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_utils.py", line 82, in collapse_excgroups
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 187, in __call__
    response = await self.dispatch_func(request, call_next)
  File "/Users/machine/Desktop/Namaskah. app/app/core/unified_rate_limiting.py", line 363, in dispatch
    response = await call_next(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 163, in call_next
    raise app_exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/base.py", line 149, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 93, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 20, in __call__
    await responder(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/gzip.py", line 39, in __call__
    await self.app(scope, receive, self.send_with_gzip)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 715, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 735, in app
    await route.handle(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/routing.py", line 288, in handle
    await self.app(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 119, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 105, in app
    response = await f(request)
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 407, in app
    content = await serialize_response(
  File "/Users/machine/Desktop/Namaskah. app/.venv/lib/python3.9/site-packages/fastapi/routing.py", line 248, in serialize_response
    raise ResponseValidationError(
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'string_type', 'loc': ('response', 'completed_at'), 'msg': 'Input should be a valid string', 'input': None}

2025-12-11 02:24:36,718 - middleware.logging - ERROR - HTTP response - server error: {'event': 'response', 'method': 'POST', 'path': '/api/verify/create', 'status_code': 500, 'process_time': 3.093, 'user_id': None, 'timestamp': 1765416276.718285}
INFO:     127.0.0.1:58743 - "POST /api/verify/create HTTP/1.1" 500 Internal Server Error
2025-12-11 02:24:38,901 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:39,308 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:43,407 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:43,408 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:43,817 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:43,818 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:48,799 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:49,345 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:49,348 - app.services.sms_polling_service - INFO - Started polling for verification 7ca0a1c7-f050-403c-bc90-c788aeb6f62d
2025-12-11 02:24:49,348 - app.services.sms_polling_service - INFO - Started polling for verification 50729c4f-1299-41e7-9598-23b2d9af32c6
2025-12-11 02:24:49,755 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:24:50,371 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:24:50,763 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:51,125 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:51,496 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:24:51,889 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:24:53,238 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:53,646 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:54,062 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:24:54,465 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:24:57,640 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:57,640 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:24:57,987 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:57,988 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:24:58,561 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:58,561 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:24:58,971 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:24:58,972 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:02,994 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:03,376 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:03,928 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:04,361 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:04,713 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:05,115 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:05,526 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:05,934 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:07,163 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:07,571 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:07,980 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:08,393 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:11,539 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:11,539 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:12,286 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:12,287 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:12,653 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:12,653 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:13,308 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:13,308 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:16,991 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:17,756 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:18,221 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:18,629 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:19,041 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:19,657 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:20,065 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:20,472 - app.services.textverified_service - WARNING - Attempt 2 failed, retrying in 2.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:21,091 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:22,007 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:22,430 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:22,934 - app.services.textverified_service - WARNING - Attempt 3 failed, retrying in 4.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:25,447 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:25,447 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:26,414 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:26,414 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

2025-12-11 02:25:26,823 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:26,824 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/7ca0a1c7-f050-403c-bc90-c788aeb6f62d:

2025-12-11 02:25:27,294 - app.services.textverified_service - ERROR - All 4 attempts failed
2025-12-11 02:25:27,294 - app.services.textverified_service - ERROR - TextVerified check error: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/50729c4f-1299-41e7-9598-23b2d9af32c6:

2025-12-11 02:25:30,837 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.comapi/pub/v2/verifications/2e565467-d8e6-41bd-b446-ab2bf3c19f0c:

2025-12-11 02:25:31,789 - app.services.textverified_service - WARNING - Attempt 1 failed, retrying in 1.0s: HTTP 404 (Not Found) for GET https://www.textverified.com/api/pub/v2/verifications/559de670-dafd-4ea8-a251-48148bca393c:

