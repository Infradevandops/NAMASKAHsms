2025-11-23T17:27:44.602284346Z 2025-11-23 17:27:44,602 - startup - INFO - Running startup initialization
2025-11-23T17:27:46.833380457Z 2025-11-23 17:27:46,833 - startup - ERROR - Database error creating admin user: (psycopg2.errors.UndefinedColumn) column users.is_moderator does not exist
2025-11-23T17:27:46.833403778Z LINE 1: ..._verifications, users.is_admin AS users_is_admin, users.is_m...
2025-11-23T17:27:46.833409108Z                                                              ^
2025-11-23T17:27:46.833411978Z 
2025-11-23T17:27:46.833416868Z [SQL: SELECT users.email AS users_email, users.password_hash AS users_password_hash, users.credits AS users_credits, users.free_verifications AS users_free_verifications, users.is_admin AS users_is_admin, users.is_moderator AS users_is_moderator, users.email_verified AS users_email_verified, users.verification_token AS users_verification_token, users.reset_token AS users_reset_token, users.reset_token_expires AS users_reset_token_expires, users.referral_code AS users_referral_code, users.referred_by AS users_referred_by, users.referral_earnings AS users_referral_earnings, users.google_id AS users_google_id, users.provider AS users_provider, users.avatar_url AS users_avatar_url, users.affiliate_id AS users_affiliate_id, users.partner_type AS users_partner_type, users.commission_tier AS users_commission_tier, users.is_affiliate AS users_is_affiliate, users.id AS users_id, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
2025-11-23T17:27:46.833420678Z FROM users 
2025-11-23T17:27:46.833424978Z WHERE users.email = %(email_1)s 
2025-11-23T17:27:46.833428808Z  LIMIT %(param_1)s]
2025-11-23T17:27:46.833431628Z [parameters: {'email_1': 'admin@namaskah.app', 'param_1': 1}]
2025-11-23T17:27:46.833434458Z (Background on this error at: https://sqlalche.me/e/20/f405)
2025-11-23T17:27:46.960960648Z 2025-11-23 17:27:46,960 - startup - INFO - Startup initialization completed
2025-11-23T17:27:47.007969754Z INFO:     Started server process [1]
2025-11-23T17:27:47.007999505Z INFO:     Waiting for application startup.
2025-11-23T17:27:47.008368974Z 2025-11-23 17:27:47,008 - startup - INFO - Application startup
2025-11-23T17:27:47.098674106Z 2025-11-23 17:27:47,098 - app.core.unified_cache - WARNING - Redis connection failed, using in - memory cache: Error 111 connecting to localhost:6379. 111.
2025-11-23T17:27:47.101913055Z 2025-11-23 17:27:47,101 - app.services.textverified_service - INFO - TextVerified client initialized successfully
2025-11-23T17:27:47.10211874Z INFO:     Application startup complete.
2025-11-23T17:27:47.102275933Z 2025-11-23 17:27:47,102 - app.services.sms_polling_service - INFO - SMS polling service started
2025-11-23T17:27:47.488897631Z 2025-11-23 17:27:47,488 - app.services.sms_polling_service - ERROR - Background service error: (psycopg2.errors.UndefinedTable) relation "verifications" does not exist
2025-11-23T17:27:47.488918001Z LINE 2: FROM verifications 
2025-11-23T17:27:47.488923321Z              ^
2025-11-23T17:27:47.488927751Z 
2025-11-23T17:27:47.488935441Z [SQL: SELECT verifications.user_id AS verifications_user_id, verifications.service_name AS verifications_service_name, verifications.phone_number AS verifications_phone_number, verifications.country AS verifications_country, verifications.capability AS verifications_capability, verifications.status AS verifications_status, verifications.verification_code AS verifications_verification_code, verifications.cost AS verifications_cost, verifications.call_duration AS verifications_call_duration, verifications.transcription AS verifications_transcription, verifications.audio_url AS verifications_audio_url, verifications.requested_carrier AS verifications_requested_carrier, verifications.requested_area_code AS verifications_requested_area_code, verifications.completed_at AS verifications_completed_at, verifications.provider AS verifications_provider, verifications.operator AS verifications_operator, verifications.pricing_tier AS verifications_pricing_tier, verifications.activation_id AS verifications_activation_id, verifications.sms_text AS verifications_sms_text, verifications.sms_code AS verifications_sms_code, verifications.sms_received_at AS verifications_sms_received_at, verifications.bulk_id AS verifications_bulk_id, verifications.id AS verifications_id, verifications.created_at AS verifications_created_at, verifications.updated_at AS verifications_updated_at 
2025-11-23T17:27:47.488955062Z FROM verifications 
2025-11-23T17:27:47.488958522Z WHERE verifications.status = %(status_1)s AND verifications.provider = %(provider_1)s]
2025-11-23T17:27:47.488961392Z [parameters: {'status_1': 'pending', 'provider_1': 'textverified'}]
2025-11-23T17:27:47.488965922Z (Background on this error at: https://sqlalche.me/e/20/f405)
2025-11-23T17:27:47.489164197Z INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
2025-11-23T17:27:47.824294298Z 2025-11-23 17:27:47,824 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'HEAD', 'url': 'http://namaskahsms.onrender.com/', 'path': '/', 'query_params': {}, 'headers': {'host': 'namaskahsms.onrender.com', 'user-agent': 'Go-http-client/1.1'}, 'client_ip': '127.0.0.1', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1763918867.8240767}
2025-11-23T17:27:47.825860017Z 2025-11-23 17:27:47,825 - app.core.unified_error_handling - WARNING - HTTPException: 405 - Method Not Allowed
2025-11-23T17:27:47.826631966Z 2025-11-23 17:27:47,826 - middleware.logging - WARNING - HTTP response - client error: {'event': 'response', 'method': 'HEAD', 'path': '/', 'status_code': 405, 'process_time': 0.002, 'user_id': None, 'timestamp': 1763918867.8264804}
2025-11-23T17:27:52.90585996Z ==> Your service is live 🎉
2025-11-23T17:27:52.934951038Z ==> 
2025-11-23T17:27:52.959490436Z ==> ///////////////////////////////////////////////////////////
2025-11-23T17:27:52.984462604Z ==> 
2025-11-23T17:27:53.009274163Z ==> Available at your primary URL https://namaskahsms.onrender.com
2025-11-23T17:27:53.03453869Z ==> 
2025-11-23T17:27:53.059598529Z ==> ///////////////////////////////////////////////////////////
2025-11-23T17:27:54.107362228Z 2025-11-23 17:27:54,107 - middleware.logging - INFO - HTTP request received: {'event': 'request', 'method': 'GET', 'url': 'https://namaskahsms.onrender.com/', 'path': '/', 'query_params': {}, 'headers': {'host': 'namaskahsms.onrender.com', 'user-agent': 'Go-http-client/2.0', 'accept-encoding': 'gzip, br', 'cdn-loop': 'cloudflare; loops=1', 'cf-connecting-ip': '35.197.80.206', 'cf-ipcountry': 'US', 'cf-ray': '9a326142dcbaec48-SEA', 'cf-visitor': '{"scheme":"https"}', 'render-proxy-ttl': '4', 'rndr-id': 'e49280ae-fe75-41f6', 'true-client-ip': '35.197.80.206', 'x-forwarded-for': '35.197.80.206, 172.71.150.53, 10.16.198.243', 'x-forwarded-proto': 'https', 'x-request-start': '1763918874104925'}, 'client_ip': '10.16.198.243', 'user_agent': '', 'user_id': None, 'user_email': None, 'timestamp': 1763918874.1070993}
2025-11-23T17:27:54.108976707Z 2025-11-23 17:27:54,108 - middleware.logging - INFO - HTTP response - success: {'event': 'response', 'method': 'GET', 'path': '/', 'status_code': 200, 'process_time': 0.002, 'user_id': None, 'timestamp': 1763918874.1087768}
2025-11-23T17:28:48.000205308Z 2025-11-23 17:28:48,000 - app.services.sms_polling_service - ERROR - Background service error: (psycopg2.errors.UndefinedTable) relation "verifications" does not exist
2025-11-23T17:28:48.000235509Z LINE 2: FROM verifications 
2025-11-23T17:28:48.000240009Z              ^
2025-11-23T17:28:48.000243419Z 
2025-11-23T17:28:48.000248689Z [SQL: SELECT verifications.user_id AS verifications_user_id, verifications.service_name AS verifications_service_name, verifications.phone_number AS verifications_phone_number, verifications.country AS verifications_country, verifications.capability AS verifications_capability, verifications.status AS verifications_status, verifications.verification_code AS verifications_verification_code, verifications.cost AS verifications_cost, verifications.call_duration AS verifications_call_duration, verifications.transcription AS verifications_transcription, verifications.audio_url AS verifications_audio_url, verifications.requested_carrier AS verifications_requested_carrier, verifications.requested_area_code AS verifications_requested_area_code, verifications.completed_at AS verifications_completed_at, verifications.provider AS verifications_provider, verifications.operator AS verifications_operator, verifications.pricing_tier AS verifications_pricing_tier, verifications.activation_id AS verifications_activation_id, verifications.sms_text AS verifications_sms_text, verifications.sms_code AS verifications_sms_code, verifications.sms_received_at AS verifications_sms_received_at, verifications.bulk_id AS verifications_bulk_id, verifications.id AS verifications_id, verifications.created_at AS verifications_created_at, verifications.updated_at AS verifications_updated_at 
2025-11-23T17:28:48.000264389Z FROM verifications 
2025-11-23T17:28:48.000267529Z WHERE verifications.status = %(status_1)s AND verifications.provider = %(provider_1)s]
2025-11-23T17:28:48.00027032Z [parameters: {'status_1': 'pending', 'provider_1': 'textverified'}]
2025-11-23T17:28:48.000274849Z (Background on this error at: https://sqlalche.me/e/20/f405)