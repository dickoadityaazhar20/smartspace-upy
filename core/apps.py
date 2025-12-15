from django.apps import AppConfig
import os


class CoreConfig(AppConfig):
    name = 'core'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Called when Django app is ready - start background scheduler and connect signals"""
        # Import signals to register them
        try:
            from core import signals  # noqa: F401
        except Exception as e:
            print(f"Warning: Could not import signals: {e}")
        
        # Only start scheduler in main process (not in migrations, etc.)
        run_main = os.environ.get('RUN_MAIN', None)
        
        # Only start in the main Django process (to avoid duplicate schedulers)
        if run_main == 'true' or run_main is None:
            try:
                from core.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                print(f"Warning: Could not start scheduler: {e}")
