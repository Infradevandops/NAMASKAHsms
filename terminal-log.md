2025-11-23T03:22:44.689582778Z          ^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.689585058Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T03:22:44.689587818Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T03:22:44.689590108Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.689592518Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T03:22:44.689663902Z     return callback(*args, **kwargs)
2025-11-23T03:22:44.689678913Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.689747316Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T03:22:44.689876373Z     run(
2025-11-23T03:22:44.689881634Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T03:22:44.690038031Z     server.run()
2025-11-23T03:22:44.690043202Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T03:22:44.690137487Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T03:22:44.778527201Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.778553292Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T03:22:44.778771834Z     return runner.run(main)
2025-11-23T03:22:44.778778594Z            ^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.778787715Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T03:22:44.778908751Z     return self._loop.run_until_complete(task)
2025-11-23T03:22:44.778931492Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.778938913Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T03:22:44.779100941Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T03:22:44.779146203Z     config.load()
2025-11-23T03:22:44.779167605Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T03:22:44.779344894Z     self.loaded_app = import_from_string(self.app)
2025-11-23T03:22:44.779381486Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.779407757Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T03:22:44.779496912Z     module = importlib.import_module(module_str)
2025-11-23T03:22:44.779576656Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.779581076Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T03:22:44.77965071Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T03:22:44.779713363Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.779739725Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T03:22:44.779743515Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T03:22:44.779746615Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T03:22:44.779749635Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T03:22:44.779755795Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T03:22:44.779759006Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T03:22:44.779761866Z   File "/app/main.py", line 6, in <module>
2025-11-23T03:22:44.779830809Z     from app.middleware.csrf_middleware import CSRFMiddleware
2025-11-23T03:22:44.779834739Z   File "/app/app/middleware/__init__.py", line 13, in <module>
2025-11-23T03:22:44.779901703Z     from .security import (
2025-11-23T03:22:44.779905473Z   File "/app/app/middleware/security.py", line 11, in <module>
2025-11-23T03:22:44.779962436Z     from app.services.auth import AuthService
2025-11-23T03:22:44.7800266Z   File "/app/app/services/__init__.py", line 6, in <module>
2025-11-23T03:22:44.780061861Z     from .notification_service import NotificationService
2025-11-23T03:22:44.780065742Z   File "/app/app/services/notification_service.py", line 18, in <module>
2025-11-23T03:22:44.780150106Z     class NotificationService(BaseService[InAppNotification]):
2025-11-23T03:22:44.780212609Z                                           ^^^^^^^^^^^^^^^^^
2025-11-23T03:22:44.780302494Z NameError: name 'InAppNotification' is not defined