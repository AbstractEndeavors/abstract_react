#!/usr/bin/env python3
from typing import *
from pathlib import Path
from functools import partial, lru_cache
from abstract_utilities import get_set_attr, is_number, make_list, safe_read_from_json, read_from_file, make_dirs, eatAll
from abstract_utilities.dynimport import import_symbols_to_parent, call_for_all_tabs
from abstract_utilities.type_utils import MIME_TYPES
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import time,  pydot, inspect, threading, enum, sys, requests, subprocess
import re,  os , shutil, shlex, tempfile, stat, faulthandler
import logging, json, clipboard, traceback, io, signal, faulthandler
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

class SharedStateBus(QObject):
    stateBroadcast = pyqtSignal(object, dict)  # (sender, state)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snap: dict = {}

    def snapshot(self) -> dict:
        return dict(self._snap)

    def push(self, sender, state: dict):
        self._snap = dict(state)
        self.stateBroadcast.emit(sender, self.snapshot())
class ConsoleBase(QWidget):
    def __init__(self, *, bus=None, parent=None):
        super().__init__(parent)
        self.bus = bus or SharedStateBus(self)
        self.setLayout(QVBoxLayout())
