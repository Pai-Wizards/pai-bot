#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio

from src.bot import main

project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    asyncio.run(main())
