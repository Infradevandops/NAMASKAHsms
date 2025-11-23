2025-11-23T03:03:06.360550341Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-11-23T03:03:06.360819316Z     rv = self.invoke(ctx)
2025-11-23T03:03:06.360847067Z          ^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.360853257Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T03:03:06.361082401Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T03:03:06.361128302Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.361151222Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T03:03:06.361341865Z     return callback(*args, **kwargs)
2025-11-23T03:03:06.361392706Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.361402926Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T03:03:06.449169259Z     run(
2025-11-23T03:03:06.4491967Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T03:03:06.449345192Z     server.run()
2025-11-23T03:03:06.449363323Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T03:03:06.449483505Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T03:03:06.449598487Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.449615947Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T03:03:06.450285439Z     return runner.run(main)
2025-11-23T03:03:06.450293729Z            ^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.450299069Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T03:03:06.450303929Z     return self._loop.run_until_complete(task)
2025-11-23T03:03:06.4503079Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.45031182Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T03:03:06.45031608Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T03:03:06.45032071Z     config.load()
2025-11-23T03:03:06.45032501Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T03:03:06.450403311Z     self.loaded_app = import_from_string(self.app)
2025-11-23T03:03:06.450561184Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.450598494Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T03:03:06.450706147Z     module = importlib.import_module(module_str)
2025-11-23T03:03:06.450749707Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.450780368Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T03:03:06.450862919Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T03:03:06.4509178Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:03:06.450946601Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T03:03:06.450950631Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T03:03:06.450953001Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T03:03:06.450965211Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T03:03:06.450967861Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T03:03:06.450975681Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T03:03:06.450979061Z   File "/app/main.py", line 6, in <module>
2025-11-23T03:03:06.451052213Z     from app.middleware.csrf_middleware import CSRFMiddleware
2025-11-23T03:03:06.451066003Z   File "/app/app/middleware/__init__.py", line 12, in <module>
2025-11-23T03:03:06.451143444Z     from .rate_limiting import AdaptiveRateLimitMiddleware, RateLimitMiddleware
2025-11-23T03:03:06.451161284Z   File "/app/app/middleware/rate_limiting.py", line 11, in <module>
2025-11-23T03:03:06.451233276Z     class RateLimitMiddleware(BaseHTTPMiddleware):
2025-11-23T03:03:06.451236946Z   File "/app/app/middleware/rate_limiting.py", line 204, in RateLimitMiddleware
2025-11-23T03:03:06.451320857Z     def _create_rate_limit_response(self, message: str) -> JSONResponse:
2025-11-23T03:03:06.451404749Z                                                            ^^^^^^^^^^^^
2025-11-23T03:03:06.451514901Z NameError: name 'JSONResponse' is not defined