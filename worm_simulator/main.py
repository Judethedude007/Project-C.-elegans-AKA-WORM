"""
⚠️  DEPRECATED: This file is no longer maintained.

This is the legacy C. elegans worm simulator. 
Please use the GPU-accelerated version instead.

╔════════════════════════════════════════════════════════════════╗
║  QUICK START                                                   ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  👉  python main_gpu.py                                        ║
║                                                                ║
│  Current version (main_gpu.py) includes:                      ║
│    ✅ GPU rendering (faster, smoother)                        ║
│    ✅ Research metrics framework                              ║
│    ✅ Ablation experiment system                              ║
│    ✅ Publication-ready data export (CSV)                     ║
│    ✅ Neural network-based behavior                           ║
│    ✅ Evolution & genetic adaptation                          ║
│    ✅ Climate system & seasons                                ║
│                                                                ║
║  DOCUMENTATION:                                               ║
║    📖 RESEARCH_GUIDE.md      - Full research workflow         ║
║    📊 plot_metrics.py        - Visualize results              ║
║    📁 IMPLEMENTATION_SUMMARY.md - System overview             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

main.py contains old code that is no longer compatible with
the current world/worm architecture. It has been deprecated
in favor of main_gpu.py.

To migrate scripts from main.py:
  1. Replace: python main.py
     With:    python main_gpu.py

  2. Check RESEARCH_GUIDE.md for new API and features
"""

import sys
print(__doc__)
print("❌ ERROR: main.py is deprecated.\n")
print("👉 Run this instead: python main_gpu.py\n")
sys.exit(1)
