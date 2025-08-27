#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installation and Setup Script for Advanced AI Module
This script helps set up the OFITEC.AI Advanced module with all dependencies
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIAdvancedInstaller:
    """Installer class for Advanced AI Module"""

    def __init__(self, odoo_path=None, addons_path=None):
        self.odoo_path = odoo_path or self._find_odoo_path()
        self.addons_path = addons_path or self._find_addons_path()
        self.module_path = Path(__file__).parent / "ofitec_ai_advanced"
        self.requirements_file = Path(__file__).parent / "requirements-ai.txt"

    def _find_odoo_path(self):
        """Find Odoo installation path"""
        common_paths = [
            "/opt/odoo",
            "/usr/local/odoo",
            "/home/odoo",
            "/var/lib/odoo",
            Path.home() / "odoo"
        ]

        for path in common_paths:
            if Path(path).exists():
                return str(path)

        # Try to find via which command
        try:
            result = subprocess.run(["which", "odoo"], capture_output=True, text=True)
            if result.returncode == 0:
                odoo_bin = Path(result.stdout.strip())
                return str(odoo_bin.parent.parent)
        except:
            pass

        return "/opt/odoo"  # Default fallback

    def _find_addons_path(self):
        """Find Odoo addons path"""
        if self.odoo_path:
            addons_path = Path(self.odoo_path) / "addons"
            if addons_path.exists():
                return str(addons_path)

        # Check common addons locations
        common_addons_paths = [
            "/opt/odoo/addons",
            "/usr/local/odoo/addons",
            "/home/odoo/addons",
            Path.home() / "odoo" / "addons"
        ]

        for path in common_addons_paths:
            if Path(path).exists():
                return str(path)

        return "/opt/odoo/addons"  # Default fallback

    def check_prerequisites(self):
        """Check system prerequisites"""
        logger.info("Checking prerequisites...")

        checks = {
            "python_version": sys.version_info >= (3, 8),
            "odoo_path": Path(self.odoo_path).exists(),
            "addons_path": Path(self.addons_path).exists(),
            "module_source": self.module_path.exists()
        }

        # Check Python packages
        required_packages = [
            "odoo", "pandas", "numpy", "scikit-learn", "xgboost", "lightgbm"
        ]

        for package in required_packages:
            try:
                __import__(package)
                checks[f"package_{package}"] = True
            except ImportError:
                checks[f"package_{package}"] = False

        # Check system tools
        system_tools = ["pip", "git", "redis-server"]
        for tool in system_tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True)
                checks[f"tool_{tool}"] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                checks[f"tool_{tool}"] = False

        return checks

    def install_python_packages(self):
        """Install required Python packages"""
        logger.info("Installing Python packages...")

        packages = [
            "scikit-learn",
            "xgboost",
            "lightgbm",
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn",
            "redis",
            "requests",
            "cryptography"
        ]

        try:
            # Create requirements file if it doesn't exist
            if not self.requirements_file.exists():
                with open(self.requirements_file, 'w') as f:
                    f.write("\n".join(packages) + "\n")
                logger.info(f"Created requirements file: {self.requirements_file}")

            # Install packages
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--user", "-r", str(self.requirements_file)
            ], check=True)

            logger.info("Python packages installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Python packages: {e}")
            return False

    def setup_redis(self):
        """Setup Redis for caching and scaling"""
        logger.info("Setting up Redis...")

        try:
            # Check if Redis is running
            result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)

            if result.returncode == 0 and "PONG" in result.stdout:
                logger.info("Redis is already running")
                return True

            # Try to start Redis service
            subprocess.run(["sudo", "systemctl", "start", "redis"], check=True)
            logger.info("Redis service started")

            # Verify Redis is working
            result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
            if result.returncode == 0 and "PONG" in result.stdout:
                return True
            else:
                logger.error("Redis failed to start properly")
                return False

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Redis setup failed: {e}")
            logger.info("Redis will need to be configured manually")
            return False

    def copy_module_files(self):
        """Copy module files to Odoo addons directory"""
        logger.info(f"Copying module to {self.addons_path}...")

        try:
            target_path = Path(self.addons_path) / "ofitec_ai_advanced"

            # Remove existing module if it exists
            if target_path.exists():
                import shutil
                shutil.rmtree(target_path)
                logger.info("Removed existing module directory")

            # Copy module files
            import shutil
            shutil.copytree(self.module_path, target_path)

            logger.info(f"Module copied to {target_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy module files: {e}")
            return False

    def create_configuration(self):
        """Create configuration files"""
        logger.info("Creating configuration files...")

        # Create AI config file
        config_dir = Path(self.addons_path) / "ofitec_ai_advanced" / "config"
        config_dir.mkdir(exist_ok=True)

        config_content = '''
# AI Module Configuration
# Generated by installation script

AI_MODELS = {
    'cost_prediction': {
        'algorithm': 'xgboost',
        'parameters': {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1
        }
    },
    'risk_assessment': {
        'algorithm': 'random_forest',
        'parameters': {
            'n_estimators': 100,
            'max_depth': 10
        }
    },
    'schedule_forecast': {
        'algorithm': 'lightgbm',
        'parameters': {
            'num_leaves': 31,
            'learning_rate': 0.1
        }
    }
}

CACHE_CONFIG = {
    'redis_host': 'localhost',
    'redis_port': 6379,
    'redis_db': 0,
    'ttl': 3600
}

FEATURE_FLAGS = {
    'enable_predictive_analytics': True,
    'enable_realtime_metrics': True,
    'enable_ml_models': True,
    'enable_api_access': True
}
'''

        config_file = config_dir / "ai_config.py"
        with open(config_file, 'w') as f:
            f.write(config_content)

        logger.info(f"Configuration file created: {config_file}")
        return True

    def update_odoo_config(self):
        """Update Odoo configuration file"""
        logger.info("Updating Odoo configuration...")

        # Common Odoo config locations
        config_paths = [
            "/etc/odoo/odoo.conf",
            "/etc/odoo.conf",
            f"{self.odoo_path}/odoo.conf",
            f"{self.odoo_path}/config/odoo.conf"
        ]

        config_file = None
        for path in config_paths:
            if Path(path).exists():
                config_file = Path(path)
                break

        if not config_file:
            logger.warning("Could not find Odoo configuration file")
            logger.info("Please manually add the addons path to your Odoo configuration")
            return False

        try:
            # Read current config
            with open(config_file, 'r') as f:
                config_content = f.read()

            # Check if addons_path is already configured
            if str(self.addons_path) not in config_content:
                # Add addons path
                if 'addons_path' in config_content:
                    # Update existing addons_path
                    lines = config_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('addons_path'):
                            lines[i] = f"addons_path = {self.odoo_path}/addons,{self.addons_path}"
                            break
                else:
                    # Add new addons_path
                    config_content += f"\naddons_path = {self.odoo_path}/addons,{self.addons_path}\n"

                # Write updated config
                with open(config_file, 'w') as f:
                    f.write(config_content)

                logger.info(f"Updated Odoo configuration: {config_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to update Odoo configuration: {e}")
            return False

    def run_post_installation(self):
        """Run post-installation tasks"""
        logger.info("Running post-installation tasks...")

        # Create log directory
        log_dir = Path("/var/log/odoo")
        log_dir.mkdir(exist_ok=True)

        # Set permissions (if running as root)
        try:
            import pwd
            odoo_user = pwd.getpwnam("odoo").pw_uid
            os.chown(log_dir, odoo_user, odoo_user)
        except:
            pass  # Ignore permission errors

        logger.info("Post-installation tasks completed")
        return True

    def install_module(self):
        """Main installation method"""
        logger.info("Starting Advanced AI Module installation...")

        # Step 1: Check prerequisites
        checks = self.check_prerequisites()
        failed_checks = [k for k, v in checks.items() if not v]

        if failed_checks:
            logger.warning("Some prerequisites are not met:")
            for check in failed_checks:
                logger.warning(f"  - {check}")
            logger.info("Installation will continue but some features may not work")

        # Step 2: Install Python packages
        if not self.install_python_packages():
            logger.error("Failed to install Python packages")
            return False

        # Step 3: Setup Redis
        self.setup_redis()  # Non-critical, continue even if it fails

        # Step 4: Copy module files
        if not self.copy_module_files():
            logger.error("Failed to copy module files")
            return False

        # Step 5: Create configuration
        if not self.create_configuration():
            logger.error("Failed to create configuration")
            return False

        # Step 6: Update Odoo config
        self.update_odoo_config()  # Non-critical

        # Step 7: Post-installation tasks
        self.run_post_installation()

        logger.info("Advanced AI Module installation completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Restart your Odoo service")
        logger.info("2. Go to Apps menu and install 'ofitec_ai_advanced'")
        logger.info("3. Configure your AI models and settings")
        logger.info("4. Start using the AI dashboard")

        return True

def main():
    """Main installation function"""
    print("OFITEC.AI Advanced Module Installer")
    print("=" * 40)

    # Get installation paths
    odoo_path = input(f"Enter Odoo installation path [{AIAdvancedInstaller().odoo_path}]: ").strip()
    addons_path = input(f"Enter Odoo addons path [{AIAdvancedInstaller().addons_path}]: ").strip()

    # Create installer
    installer = AIAdvancedInstaller(
        odoo_path=odoo_path if odoo_path else None,
        addons_path=addons_path if addons_path else None
    )

    # Run installation
    if installer.install_module():
        print("\n✅ Installation completed successfully!")
        return 0
    else:
        print("\n❌ Installation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
