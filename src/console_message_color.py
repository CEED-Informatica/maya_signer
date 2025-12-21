# -*- coding: utf-8 -*-

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

def info(text: str = '[INFO]') -> str:
  return f"{BLUE}{text}{NC}"

def error(text: str= '[ERROR]') -> str:
  return f"{RED}{text}{NC}"

def ok(text: str = '[OK]') -> str:
  return f"{GREEN}{text}{NC}"

def warning(text: str = '[WARNING]') -> str:
  return f"{YELLOW}{text}{NC}"
