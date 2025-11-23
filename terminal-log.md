2025-11-23T14:04:31.844297429Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.844299379Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.844301409Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.844303519Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.84430557Z     return await anext(self.gen)
2025-11-23T14:04:31.84430753Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.84431252Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.8443151Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.84431733Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.84431938Z     return await anext(self.gen)
2025-11-23T14:04:31.84432142Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.84432339Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.84432578Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.84432785Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.84432992Z     return await anext(self.gen)
2025-11-23T14:04:31.84433227Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.84433431Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.84433629Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.84433832Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.84434027Z     return await anext(self.gen)
2025-11-23T14:04:31.84434219Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.84434411Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.844346171Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.844348331Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.84435044Z     return await anext(self.gen)
2025-11-23T14:04:31.8443524Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.844354451Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.844356531Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.844358601Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.844360531Z     return await anext(self.gen)
2025-11-23T14:04:31.844362591Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.844364671Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.844366591Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.844373161Z   File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
2025-11-23T14:04:31.844375441Z     return await anext(self.gen)
2025-11-23T14:04:31.844377411Z            ^^^^^^^^^^^^^^^^^^^^^
2025-11-23T14:04:31.844379401Z   File "/home/appuser/.local/lib/python3.11/site-packages/fastapi/routing.py", line 133, in merged_lifespan
2025-11-23T14:04:31.844381371Z     async with original_context(app) as maybe_original_state:
2025-11-23T14:04:31.844383351Z   File "/home/appuser/.local/lib/python3.11/site-packages/starlette/routing.py", line 569, in __aenter__
2025-11-23T14:04:31.844385391Z     await self._router.startup()
2025-11-23T14:04:31.844387341Z   File "/home/appuser/.local/lib/python3.11/site-packages/starlette/routing.py", line 670, in startup
2025-11-23T14:04:31.844390121Z     await handler()
2025-11-23T14:04:31.844392092Z   File "/app/main.py", line 377, in startup_event
2025-11-23T14:04:31.844394081Z     from app.services.sms_polling_service import sms_polling_service
2025-11-23T14:04:31.844396132Z   File "/app/app/services/sms_polling_service.py", line 10, in <module>
2025-11-23T14:04:31.844398352Z     logger = get_logger(__name__)
2025-11-23T14:04:31.844400282Z              ^^^^^^^^^^
2025-11-23T14:04:31.844402332Z NameError: name 'get_logger' is not defined
2025-11-23T14:04:31.844404102Z 
2025-11-23T14:04:31.844411232Z ERROR:    Application startup failed. Exiting.