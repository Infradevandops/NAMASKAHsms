import traceback
try:
    from app.services.providers.provider_router import ProviderRouter
    print("ProviderRouter imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
