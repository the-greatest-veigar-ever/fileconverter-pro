#!/usr/bin/env python3
"""
System Dependencies Checker for FileConverter Pro
This script verifies that all required system dependencies are installed and properly configured.
"""

import os
import sys
import subprocess
import shutil
import pkg_resources
from typing import Dict, List, Tuple

class DependencyChecker:
    def __init__(self):
        self.all_passed = True
        self.warnings = []
        self.errors = []
        
    def check_command(self, command: str, name: str) -> bool:
        """Check if a command is available in the system PATH."""
        if shutil.which(command) is None:
            self.errors.append(f"❌ {name} not found. Please install it first.")
            self.all_passed = False
            return False
        return True
    
    def check_library(self, library: str) -> bool:
        """Check if a system library is installed."""
        try:
            import ctypes
            ctypes.CDLL(library)
            return True
        except OSError:
            self.errors.append(f"❌ Library {library} not found.")
            self.all_passed = False
            return False
            
    def check_python_package(self, package: str) -> bool:
        """Check if a Python package is installed."""
        try:
            # First try importing
            module_name = package.replace('-', '_').split('>=')[0].split('==')[0]
            print(f"Checking for package {package} (module: {module_name})")
            
            # Try pkg_resources first
            try:
                pkg_resources.get_distribution(package)
                print(f"✅ Found {package} using pkg_resources")
                return True
            except pkg_resources.DistributionNotFound:
                print(f"Not found via pkg_resources: {package}")
            
            # Try direct import as fallback
            __import__(module_name)
            print(f"✅ Successfully imported {module_name}")
            return True
            
        except ImportError as e:
            print(f"Import error for {module_name}: {str(e)}")
            self.errors.append(f"❌ Python package {package} not found. Install it with pip.")
            self.all_passed = False
            return False

    def check_imagemagick(self):
        """Check ImageMagick installation and configuration."""
        if not self.check_command('convert', 'ImageMagick'):
            return
        
        try:
            # Check version
            result = subprocess.run(['convert', '-version'], 
                                 capture_output=True, text=True)
            version = result.stdout.split('\n')[0]
            print(f"✅ ImageMagick found: {version}")
            
            # Check policy file
            policy_paths = [
                '/etc/ImageMagick-6/policy.xml',
                '/etc/ImageMagick-7/policy.xml',
                '/usr/local/etc/ImageMagick-6/policy.xml',
                '/usr/local/etc/ImageMagick-7/policy.xml',
                '/opt/homebrew/etc/ImageMagick-7/policy.xml',
                '/opt/homebrew/Cellar/imagemagick/*/etc/ImageMagick-7/policy.xml'
            ]
            
            policy_found = False
            for path in policy_paths:
                # Handle wildcard paths
                if '*' in path:
                    import glob
                    matching_paths = glob.glob(path)
                    for matched_path in matching_paths:
                        if os.path.exists(matched_path):
                            policy_found = True
                            print(f"✅ ImageMagick policy file found at: {matched_path}")
                            break
                elif os.path.exists(path):
                    policy_found = True
                    print(f"✅ ImageMagick policy file found at: {path}")
                    break
                    
            if not policy_found:
                self.warnings.append("⚠️ ImageMagick policy file not found in standard locations")
                
        except subprocess.CalledProcessError:
            self.errors.append("❌ Error checking ImageMagick configuration")
            self.all_passed = False

    def check_ffmpeg(self):
        """Check FFmpeg installation and codecs."""
        if not self.check_command('ffmpeg', 'FFmpeg'):
            return
            
        try:
            # Check version and codecs
            result = subprocess.run(['ffmpeg', '-codecs'], 
                                 capture_output=True, text=True)
            
            # Check for common codecs
            codecs = ['libx264', 'libx265', 'aac', 'libvorbis']
            missing_codecs = []
            
            for codec in codecs:
                if codec not in result.stdout:
                    missing_codecs.append(codec)
            
            if missing_codecs:
                self.warnings.append(f"⚠️ FFmpeg is missing some codecs: {', '.join(missing_codecs)}")
            else:
                print("✅ FFmpeg found with all required codecs")
                
        except subprocess.CalledProcessError:
            self.errors.append("❌ Error checking FFmpeg configuration")
            self.all_passed = False

    def check_libreoffice(self):
        """Check LibreOffice installation and headless mode."""
        if not self.check_command('soffice', 'LibreOffice'):
            return
            
        try:
            # Check headless mode
            result = subprocess.run(['soffice', '--help'], 
                                 capture_output=True, text=True)
            
            if '--headless' in result.stdout:
                print("✅ LibreOffice found with headless mode support")
            else:
                self.warnings.append("⚠️ LibreOffice might not support headless mode")
                
        except subprocess.CalledProcessError:
            self.errors.append("❌ Error checking LibreOffice configuration")
            self.all_passed = False

    def check_archive_tools(self):
        """Check archive handling tools."""
        tools = {
            '7z': '7-Zip',
            'unar': 'UnRAR',  # Changed from unrar to unar
            'zip': 'ZIP'
        }
        
        for command, name in tools.items():
            if self.check_command(command, name):
                print(f"✅ {name} found")

    def check_python_dependencies(self):
        """Check required Python packages."""
        print("\nPython Environment Information:")
        print(f"Python Path: {sys.executable}")
        print(f"Python Version: {sys.version}")
        
        packages = [
            'Pillow',
            'wand',
            'python-magic',
            'filetype',
            'ffmpeg-python',
            'python-docx',
            'openpyxl',
            'PyPDF2',
            'pandoc',
            'python-pptx'
        ]
        
        print("\nChecking Python packages:")
        for package in packages:
            if self.check_python_package(package):
                print(f"✅ Python package {package} found")

    def run_all_checks(self):
        """Run all dependency checks."""
        print("\n=== Checking System Dependencies ===\n")
        
        # Check core dependencies
        self.check_imagemagick()
        self.check_ffmpeg()
        self.check_libreoffice()
        self.check_archive_tools()
        
        print("\n=== Checking Python Dependencies ===\n")
        self.check_python_dependencies()
        
        # Print summary
        print("\n=== Summary ===\n")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(warning)
                
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(error)
        
        if self.all_passed:
            print("\n✅ All dependency checks passed!")
            return 0
        else:
            print("\n❌ Some dependency checks failed. Please install missing dependencies.")
            return 1

def main():
    checker = DependencyChecker()
    sys.exit(checker.run_all_checks())

if __name__ == '__main__':
    main() 