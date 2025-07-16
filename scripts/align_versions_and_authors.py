#!/usr/bin/env python3
"""
Version and Author Alignment Script
Automatically updates all production files to use:
- Version: 2.2.0
- Author: Alexandre Huther
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

class VersionAuthorAligner:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.target_version = "2.2.0"
        self.target_author = "Alexandre Huther"
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Files to skip (non-production)
        self.skip_patterns = [
            'scripts/sandbox/',
            'scripts/debug_',
            'scripts/test_',
            'scripts/archive/',
            'data/temp/',
            'data/debug/',
            'logs/',
            'venv/',
            '__pycache__/',
            '.git/',
            'node_modules/',
            'htmlcov/',
            '.pytest_cache/',
            'documentation_version_assessment.py'
        ]
        
        # Version patterns to replace
        self.version_patterns = {
            'python': [
                (r'version\s*[=:]\s*["\']([^"\']+)["\']', 'version = "2.2.0"'),
                (r'__version__\s*[=:]\s*["\']([^"\']+)["\']', '__version__ = "2.2.0"'),
            ],
            'yaml': [
                (r'version\s*:\s*([^\s]+)', 'version = "2.2.0"'),
            ],
            'json': [
                (r'"version"\s*:\s*"([^"]+)"', '"version": "2.2.0"'),
            ],
            'markdown': [
                (r'\*\*Version\s*:\s*([^*]+)\*\*', '**Version: 2.2.0**'),
                (r'Version\s*:\s*([^\n]+)', 'Version: 2.2.0'),
                (r'Current Version\s*:\s*([^\n]+)', 'Current Version: 2.2.0'),
            ],
            'typescript': [
                (r'version\s*[=:]\s*["\']([^"\']+)["\']', 'version = "2.2.0"'),
            ],
            'javascript': [
                (r'version\s*[=:]\s*["\']([^"\']+)["\']', 'version = "2.2.0"'),
            ]
        }
        
        # Author patterns to replace
        self.author_patterns = {
            'python': [
                (r'author\s*[=:]\s*["\']([^"\']+)["\']', 'author = "Alexandre Huther"'),
            ],
            'yaml': [
                (r'author\s*:\s*([^\s]+)', 'author = "Alexandre Huther"'),
            ],
            'json': [
                (r'"author"\s*:\s*"([^"]+)"', '"author": "Alexandre Huther"'),
            ],
            'markdown': [
                (r'\*\*Author\s*:\s*([^*]+)\*\*', '**Author: Alexandre Huther**'),
                (r'Author\s*:\s*([^\n]+)', 'Author: Alexandre Huther'),
            ],
            'typescript': [
                (r'author\s*[=:]\s*["\']([^"\']+)["\']', 'author = "Alexandre Huther"'),
            ],
            'javascript': [
                (r'author\s*[=:]\s*["\']([^"\']+)["\']', 'author = "Alexandre Huther"'),
            ]
        }
    
    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped (non-production)."""
        for pattern in self.skip_patterns:
            if pattern in file_path:
                return True
        return False
    
    def get_file_type(self, file_path: str) -> str:
        """Determine file type for pattern matching."""
        ext = Path(file_path).suffix.lower()
        if ext == '.py':
            return 'python'
        elif ext in ['.yml', '.yaml']:
            return 'yaml'
        elif ext == '.json':
            return 'json'
        elif ext == '.md':
            return 'markdown'
        elif ext in ['.ts', '.tsx']:
            return 'typescript'
        elif ext in ['.js', '.jsx']:
            return 'javascript'
        else:
            return 'unknown'
    
    def add_version_header_to_markdown(self, content: str, file_path: str) -> str:
        """Add standard version header to markdown files."""
        # Check if file already has version header
        if re.search(r'\*\*Version\s*:\s*2\.2\.0\*\*', content):
            return content
        
        # Add header at the beginning
        header = f"""# {Path(file_path).stem.replace('_', ' ').title()}

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: {self.current_date}**

"""
        
        # If file already has a title, replace it
        if content.startswith('# '):
            lines = content.split('\n')
            if len(lines) > 1:
                return header + '\n'.join(lines[1:])
        
        return header + content
    
    def update_file_versions_and_authors(self, file_path: str, dry_run: bool = True) -> Dict[str, any]:
        """Update version and author information in a file."""
        result = {
            'file': file_path,
            'changes_made': False,
            'version_updated': False,
            'author_updated': False,
            'header_added': False,
            'errors': []
        }
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_type = self.get_file_type(file_path)
            
            # Update versions
            if file_type in self.version_patterns:
                for pattern, replacement in self.version_patterns[file_type]:
                    if re.search(pattern, content, re.IGNORECASE):
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                        result['version_updated'] = True
                        result['changes_made'] = True
            
            # Update authors
            if file_type in self.author_patterns:
                for pattern, replacement in self.author_patterns[file_type]:
                    if re.search(pattern, content, re.IGNORECASE):
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                        result['author_updated'] = True
                        result['changes_made'] = True
            
            # Add version header to markdown files
            if file_type == 'markdown' and not re.search(r'\*\*Version\s*:\s*2\.2\.0\*\*', content):
                content = self.add_version_header_to_markdown(content, file_path)
                result['header_added'] = True
                result['changes_made'] = True
            
            # Write changes if not dry run
            if not dry_run and result['changes_made']:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def find_production_files(self) -> List[str]:
        """Find all production files that need updating."""
        production_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip non-production directories
            dirs[:] = [d for d in dirs if not any(pattern in str(Path(root) / d) for pattern in self.skip_patterns)]
            
            for file in files:
                file_path = str(Path(root) / file)
                rel_path = str(Path(file_path).relative_to(self.project_root))
                
                if not self.should_skip_file(rel_path):
                    # Only include files with known extensions
                    if self.get_file_type(rel_path) != 'unknown':
                        production_files.append(rel_path)
        
        return production_files
    
    def run_alignment(self, dry_run: bool = True) -> Dict[str, any]:
        """Run the version and author alignment process."""
        print(f"🔍 Starting Version and Author Alignment...")
        print(f"Target Version: {self.target_version}")
        print(f"Target Author: {self.target_author}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        print()
        
        # Find production files
        production_files = self.find_production_files()
        print(f"📁 Found {len(production_files)} production files to process")
        
        # Process files
        results = []
        files_with_changes = 0
        version_updates = 0
        author_updates = 0
        header_additions = 0
        
        for file_path in production_files:
            result = self.update_file_versions_and_authors(file_path, dry_run)
            results.append(result)
            
            if result['changes_made']:
                files_with_changes += 1
                print(f"✅ {file_path}")
                if result['version_updated']:
                    version_updates += 1
                    print(f"   📝 Version updated")
                if result['author_updated']:
                    author_updates += 1
                    print(f"   👤 Author updated")
                if result['header_added']:
                    header_additions += 1
                    print(f"   📋 Header added")
            else:
                print(f"⏭️  {file_path} (no changes needed)")
        
        # Summary
        print()
        print("="*60)
        print("📊 ALIGNMENT SUMMARY")
        print("="*60)
        print(f"📁 Total files processed: {len(production_files)}")
        print(f"✅ Files with changes: {files_with_changes}")
        print(f"📝 Version updates: {version_updates}")
        print(f"👤 Author updates: {author_updates}")
        print(f"📋 Header additions: {header_additions}")
        
        if dry_run:
            print(f"\n💡 This was a DRY RUN. Run with dry_run=False to apply changes.")
        
        return {
            'total_files': len(production_files),
            'files_with_changes': files_with_changes,
            'version_updates': version_updates,
            'author_updates': author_updates,
            'header_additions': header_additions,
            'results': results
        }

def main():
    """Main function."""
    aligner = VersionAuthorAligner()
    
    # First run: dry run to see what would be changed
    print("🔍 DRY RUN - Previewing changes...")
    dry_run_results = aligner.run_alignment(dry_run=True)
    
    # Ask for confirmation
    if dry_run_results['files_with_changes'] > 0:
        print(f"\n❓ Apply changes to {dry_run_results['files_with_changes']} files? (y/N): ", end="")
        response = input().strip().lower()
        
        if response in ['y', 'yes']:
            print("\n🚀 Applying changes...")
            live_results = aligner.run_alignment(dry_run=False)
            
            # Save results
            with open('docs/VERSION_AUTHOR_ALIGNMENT_RESULTS.json', 'w') as f:
                json.dump({
                    'dry_run': dry_run_results,
                    'live_run': live_results,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"\n📄 Results saved to: docs/VERSION_AUTHOR_ALIGNMENT_RESULTS.json")
        else:
            print("❌ Changes cancelled.")
    else:
        print("✅ No changes needed - all files are already aligned!")

if __name__ == "__main__":
    main() 