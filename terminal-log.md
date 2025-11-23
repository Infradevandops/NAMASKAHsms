2025-11-23T14:35:53.703345817Z #17 sha256:4f8e39fcd7def659803b9ba5c4b332c25abe5c688fed673600b470855ae3bd2c 93.52MB / 93.52MB 0.6s done
2025-11-23T14:35:53.860637362Z #17 extracting sha256:4f8e39fcd7def659803b9ba5c4b332c25abe5c688fed673600b470855ae3bd2c
2025-11-23T14:35:56.726107411Z #17 extracting sha256:4f8e39fcd7def659803b9ba5c4b332c25abe5c688fed673600b470855ae3bd2c 3.0s done
2025-11-23T14:35:56.94705371Z #17 sha256:40dc4096077e3ce5c02643e9e53f6ffcbcade228dcfe743abbad68556d75599b 698B / 698B done
2025-11-23T14:35:56.947074031Z #17 extracting sha256:40dc4096077e3ce5c02643e9e53f6ffcbcade228dcfe743abbad68556d75599b 0.0s done
2025-11-23T14:35:56.958893578Z #17 sha256:c506d1ead3454791d00e8bec5ec2a1014ee6d7bc5b24a088538dae6b7795e8e7 32.51MB / 61.26MB 0.2s
2025-11-23T14:35:57.108717562Z #17 sha256:c506d1ead3454791d00e8bec5ec2a1014ee6d7bc5b24a088538dae6b7795e8e7 61.26MB / 61.26MB 0.3s
2025-11-23T14:35:57.237550751Z #17 sha256:c506d1ead3454791d00e8bec5ec2a1014ee6d7bc5b24a088538dae6b7795e8e7 61.26MB / 61.26MB 0.4s done
2025-11-23T14:35:57.39569221Z #17 extracting sha256:c506d1ead3454791d00e8bec5ec2a1014ee6d7bc5b24a088538dae6b7795e8e7
2025-11-23T14:36:01.073162477Z #17 extracting sha256:c506d1ead3454791d00e8bec5ec2a1014ee6d7bc5b24a088538dae6b7795e8e7 3.8s done
2025-11-23T14:36:01.231916276Z #17 writing cache image manifest sha256:8a9173d96c7c71308009342f4df46c05b75dc559df9565a15b38ec6a6d5e5e68 0.0s done
2025-11-23T14:36:01.231937596Z #17 DONE 8.2s
2025-11-23T14:36:01.567637367Z Pushing image to registry...
2025-11-23T14:36:03.349770169Z Upload succeeded
2025-11-23T14:36:04.971749944Z ==> Deploying...
2025-11-23T14:36:26.237667848Z ⚠️ Warning: SECRET_KEY appears to be a weak or default value
2025-11-23T14:36:26.2377012Z ⚠️ Warning: JWT_SECRET_KEY appears to be a weak or default value
2025-11-23T14:36:33.813964605Z Basic logging configured (structlog disabled for debugging)
2025-11-23T14:36:34.122604651Z 2025-11-23 14:36:34,122 - startup - INFO - Running startup initialization
2025-11-23T14:37:21.201295056Z ==> No open ports detected, continuing to scan...
2025-11-23T14:37:21.327379441Z ==> Docs on specifying a port: https://render.com/docs/web-services#port-binding
2025-11-23T14:37:35.049236713Z 2025-11-23 14:37:35,049 - startup - ERROR - Database error creating admin user: (psycopg2.OperationalError) SSL connection has been closed unexpectedly
2025-11-23T14:37:35.049284315Z 
2025-11-23T14:37:35.049290926Z (Background on this error at: https://sqlalche.me/e/20/e3q8)
2025-11-23T14:37:35.049416493Z 2025-11-23 14:37:35,049 - startup - INFO - Startup initialization completed
2025-11-23T14:37:35.127547599Z INFO:     Started server process [1]
2025-11-23T14:37:35.127577261Z INFO:     Waiting for application startup.
2025-11-23T14:37:35.128006006Z 2025-11-23 14:37:35,127 - startup - INFO - Application startup
2025-11-23T14:37:35.215749625Z 2025-11-23 14:37:35,215 - app.core.unified_cache - WARNING - Redis connection failed, using in - memory cache: Error 111 connecting to localhost:6379. 111.
2025-11-23T14:37:35.219218258Z 2025-11-23 14:37:35,219 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-11-23T14:37:35.219462532Z INFO:     Application startup complete.
2025-11-23T14:37:35.219623812Z 2025-11-23 14:37:35,219 - app.services.sms_polling_service - INFO - SMS polling service started
2025-11-23T14:38:22.700887937Z ==> No open ports detected, continuing to scan...
2025-11-23T14:38:22.818205373Z ==> Docs on specifying a port: https://render.com/docs/web-services#port-binding
2025-11-23T14:38:36.165654651Z 2025-11-23 14:38:36,165 - app.services.sms_polling_service - ERROR - Background service error: (psycopg2.OperationalError) SSL connection has been closed unexpectedly
2025-11-23T14:38:36.165674302Z 
2025-11-23T14:38:36.165682273Z (Background on this error at: https://sqlalche.me/e/20/e3q8)
2025-11-23T14:38:36.166037384Z INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
2025-11-23T14:38:36.611670143Z 2025-11-23 14:38:36,611 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'HEAD', 'url': 'http://namaskahsms.onrender.com/', 'path': '/', 'query_params': {}, 'headers': {'host': 'namaskahsms.onrender.com', 'user-agent': 'Go-http-client/1.1'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1763908716.6114552}
2025-11-23T14:38:36.61282026Z 2025-11-23 14:38:36,612 - app.core.unified_error_handling - WARNING - HTTPException: 405 - Method Not Allowed
2025-11-23T14:38:36.613611627Z 2025-11-23 14:38:36,613 - middleware.logging - WARNING - HTTP response - client error: {'event': 'response', 'method': 'HEAD', 'path': '/', 'status_code': 405, 'process_time': 0.002, 'user_id': None, 'timestamp': 1763908716.613424}
2025-11-23T14:38:42.001534346Z ==> Your service is live 🎉
2025-11-23T14:38:42.029457464Z ==> 
2025-11-23T14:38:42.055584482Z ==> ///////////////////////////////////////////////////////////
2025-11-23T14:38:42.07896414Z ==> 
2025-11-23T14:38:42.104885118Z ==> Available at your primary URL https://namaskahsms.onrender.com
2025-11-23T14:38:42.129481176Z ==> 
2025-11-23T14:38:42.152915354Z ==> ///////////////////////////////////////////////////////////
2025-11-23T14:38:42.958396123Z 2025-11-23 14:38:42,958 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'https://namaskahsms.onrender.com/', 'path': '/', 'query_params': {}, 'headers': {'host': 'namaskahsms.onrender.com', 'user-agent': 'Go-http-client/2.0', 'accept-encoding': 'gzip, br', 'cdn-loop': 'cloudflare; loops=1', 'cf-connecting-ip': '34.82.242.193', 'cf-ipcountry': 'US', 'cf-ray': '9a31696e2ba0ec88-SEA', 'cf-visitor': '{"scheme":"https"}', 'render-proxy-ttl': '4', 'rndr-id': '0b34ee2b-79ed-4a54', 'true-client-ip': '34.82.242.193', 'x-forwarded-for': '34.82.242.193, 172.71.150.52, 10.17.242.57', 'x-forwarded-proto': 'https', 'x-request-start': '1763908722951248'}, 'client_ip': '10.17.242.57', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1763908722.9581535}
2025-11-23T14:38:42.959615364Z 2025-11-23 14:38:42,959 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/', 'status_code': 200, 'process_time': 0.001, 'user_id': None, 'timestamp': 1763908722.9594932}