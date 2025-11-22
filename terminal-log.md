2025-11-22T18:11:39.514780488Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-22T18:11:39.514950702Z     server.run()
2025-11-22T18:11:39.514956753Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-22T18:11:39.515055646Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-22T18:11:39.515121478Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:39.515168879Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-22T18:11:39.515288052Z     return runner.run(main)
2025-11-22T18:11:39.515303213Z            ^^^^^^^^^^^^^^^^
2025-11-22T18:11:39.515348644Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-22T18:11:39.515447547Z     return self._loop.run_until_complete(task)
2025-11-22T18:11:39.515496649Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:39.515520639Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-22T18:11:39.515723605Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-22T18:11:39.515809768Z     config.load()
2025-11-22T18:11:39.515815088Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-22T18:11:39.515983973Z     self.loaded_app = import_from_string(self.app)
2025-11-22T18:11:39.516048965Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:39.516106606Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-22T18:11:39.516257741Z     module = importlib.import_module(module_str)
2025-11-22T18:11:39.516263451Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:39.516279921Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-22T18:11:39.516459637Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-22T18:11:39.51658109Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:39.516630431Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-22T18:11:39.516634572Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-22T18:11:39.516637592Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-22T18:11:39.516640342Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-22T18:11:39.516643362Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-22T18:11:39.516645912Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-22T18:11:39.516658552Z   File "/app/main.py", line 23, in <module>
2025-11-22T18:11:39.516750395Z     from app.api.core.auth import router as auth_router
2025-11-22T18:11:39.516756525Z   File "/app/app/api/core/auth.py", line 10, in <module>
2025-11-22T18:11:39.516878089Z     from app.schemas import (
2025-11-22T18:11:39.516881959Z   File "/app/app/schemas/__init__.py", line 35, in <module>
2025-11-22T18:11:39.51691893Z     from .auth import (
2025-11-22T18:11:39.51692414Z   File "/app/app/schemas/auth.py", line 21
2025-11-22T18:11:39.516938791Z     referral_code: Optional[str] = Field(None, description="Optional referral code)
2025-11-22T18:11:39.516990952Z                                                            ^
2025-11-22T18:11:39.516994872Z SyntaxError: unterminated string literal (detected at line 21)
2025-11-22T18:11:42.160879987Z ==> Exited with status 1
2025-11-22T18:11:42.177171395Z ==> Common ways to troubleshoot your deploy: https://render.com/docs/troubleshooting-deploys
2025-11-22T18:11:46.408853392Z ⚠️ Warning: SECRET_KEY appears to be a weak or default value
2025-11-22T18:11:46.408874852Z ⚠️ Warning: JWT_SECRET_KEY appears to be a weak or default value
2025-11-22T18:11:52.713626965Z Traceback (most recent call last):
2025-11-22T18:11:52.713642146Z   File "/home/appuser/.local/bin/uvicorn", line 8, in <module>
2025-11-22T18:11:52.713652906Z     sys.exit(main())
2025-11-22T18:11:52.713689097Z              ^^^^^^
2025-11-22T18:11:52.713695187Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
2025-11-22T18:11:52.713956325Z     return self.main(*args, **kwargs)
2025-11-22T18:11:52.713997956Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.714209742Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-11-22T18:11:52.714349026Z     rv = self.invoke(ctx)
2025-11-22T18:11:52.714386737Z          ^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.714392777Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-22T18:11:52.714613414Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-22T18:11:52.714645155Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.714668636Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-22T18:11:52.714894972Z     return callback(*args, **kwargs)
2025-11-22T18:11:52.714933263Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.714980595Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-22T18:11:52.715105988Z     run(
2025-11-22T18:11:52.715111188Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-22T18:11:52.715253402Z     server.run()
2025-11-22T18:11:52.715258503Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-22T18:11:52.801202277Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-22T18:11:52.80130676Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.801346031Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-22T18:11:52.802227577Z     return runner.run(main)
2025-11-22T18:11:52.802233077Z            ^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.802236507Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-22T18:11:52.802301619Z     return self._loop.run_until_complete(task)
2025-11-22T18:11:52.802386161Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.802441313Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-22T18:11:52.802554366Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-22T18:11:52.802625608Z     config.load()
2025-11-22T18:11:52.802658109Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-22T18:11:52.802813444Z     self.loaded_app = import_from_string(self.app)
2025-11-22T18:11:52.802858725Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.802869775Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-22T18:11:52.802962148Z     module = importlib.import_module(module_str)
2025-11-22T18:11:52.8030233Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.80302913Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-22T18:11:52.80371316Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-22T18:11:52.803788912Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-22T18:11:52.803805613Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-22T18:11:52.803808523Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-22T18:11:52.803813253Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-22T18:11:52.803819513Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-22T18:11:52.803830983Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-22T18:11:52.803836594Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-22T18:11:52.803839814Z   File "/app/main.py", line 23, in <module>
2025-11-22T18:11:52.803924316Z     from app.api.core.auth import router as auth_router
2025-11-22T18:11:52.803960637Z   File "/app/app/api/core/auth.py", line 10, in <module>
2025-11-22T18:11:52.80405557Z     from app.schemas import (
2025-11-22T18:11:52.80405851Z   File "/app/app/schemas/__init__.py", line 35, in <module>
2025-11-22T18:11:52.804151933Z     from .auth import (
2025-11-22T18:11:52.804156363Z   File "/app/app/schemas/auth.py", line 21
2025-11-22T18:11:52.804159163Z     referral_code: Optional[str] = Field(None, description="Optional referral code)
2025-11-22T18:11:52.804226475Z                                                            ^
2025-11-22T18:11:52.804237065Z SyntaxError: unterminated string literal (detected at line 21)