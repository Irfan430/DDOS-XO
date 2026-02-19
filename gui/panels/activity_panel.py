# Path: gui/panels/activity_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QScrollArea, QProgressBar, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QIcon
import qtawesome as qta

class LiveActivityPanel(QFrame):
    """
    LUNA-ULTRA Live Agent Activity Panel: Displays real-time execution awareness.
    Refined for Professional Engineering Mode: Supports standardized TaskResult rendering.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setObjectName("Panel")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header_icon = QLabel()
        header_icon.setPixmap(qta.icon("fa5s.broadcast-tower", color="#5850EC").pixmap(18, 18))
        header_layout.addWidget(header_icon)
        header_layout.addWidget(QLabel("LIVE AGENT ACTIVITY", objectName="SubHeader"))
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Active Agent Card
        self.agent_card = QFrame()
        self.agent_card.setStyleSheet("background-color: #111114; border-radius: 10px; border: 1px solid #1F1F23;")
        agent_layout = QVBoxLayout(self.agent_card)
        
        self.active_agent_lbl = QLabel("Active Agent: IDLE")
        self.active_agent_lbl.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 14px;")
        agent_layout.addWidget(self.active_agent_lbl)
        
        self.current_task_lbl = QLabel("Current Task: Waiting for input...")
        self.current_task_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        self.current_task_lbl.setWordWrap(True)
        agent_layout.addWidget(self.current_task_lbl)
        
        layout.addWidget(self.agent_card)

        # Metrics Grid
        metrics_layout = QHBoxLayout()
        
        # Confidence Score
        conf_box = QVBoxLayout()
        conf_box.addWidget(QLabel("CONFIDENCE", objectName="SubHeader"))
        self.conf_score = QLabel("0.00")
        self.conf_score.setStyleSheet("font-size: 18px; font-weight: 800; color: #5850EC;")
        conf_box.addWidget(self.conf_score)
        metrics_layout.addLayout(conf_box)
        
        # Risk Level
        risk_box = QVBoxLayout()
        risk_box.addWidget(QLabel("RISK LEVEL", objectName="SubHeader"))
        self.risk_indicator = QLabel("LOW")
        self.risk_indicator.setStyleSheet("font-size: 18px; font-weight: 800; color: #10B981;")
        risk_box.addWidget(self.risk_indicator)
        metrics_layout.addLayout(risk_box)
        
        layout.addLayout(metrics_layout)

        # Execution Timeline
        layout.addWidget(QLabel("EXECUTION TIMELINE", objectName="SubHeader"))
        self.timeline = QListWidget()
        self.timeline.setStyleSheet("background: transparent; border: none; color: #E2E2E9;")
        self.timeline.setSpacing(5)
        layout.addWidget(self.timeline)

        layout.addStretch()

    def update_activity(self, data: dict):
        """Updates the panel with standardized execution data."""
        agent = data.get("agent", "IDLE")
        # Handle both 'task' and 'message' for compatibility
        task = data.get("task") or data.get("message") or "Processing..."
        confidence = data.get("confidence", 0.00)
        risk = data.get("risk_level", "LOW")
        status = data.get("status", "pending").lower()

        self.active_agent_lbl.setText(f"Active Agent: {agent.upper()}")
        self.current_task_lbl.setText(f"Current Task: {task}")
        self.conf_score.setText(f"{confidence:.2f}")
        
        # Update Risk Color
        self.risk_indicator.setText(risk.upper())
        if risk.upper() == "HIGH" or risk.upper() == "CRITICAL":
            self.risk_indicator.setStyleSheet("font-size: 18px; font-weight: 800; color: #EF4444;")
        elif risk.upper() == "MEDIUM":
            self.risk_indicator.setStyleSheet("font-size: 18px; font-weight: 800; color: #F59E0B;")
        else:
            self.risk_indicator.setStyleSheet("font-size: 18px; font-weight: 800; color: #10B981;")

        # Add to Timeline
        item_text = f"[{agent.upper()}] {task}"
        item = QListWidgetItem(item_text)
        
        if status == "success":
            item.setForeground(QColor("#10B981"))
            item.setIcon(qta.icon("fa5s.check-circle", color="#10B981"))
        elif status == "failed":
            item.setForeground(QColor("#EF4444"))
            item.setIcon(qta.icon("fa5s.times-circle", color="#EF4444"))
        elif status == "partial":
            item.setForeground(QColor("#F59E0B"))
            item.setIcon(qta.icon("fa5s.exclamation-circle", color="#F59E0B"))
        elif status == "executing":
            item.setForeground(QColor("#3B82F6"))
            item.setIcon(qta.icon("fa5s.spinner", color="#3B82F6"))
        else:
            item.setIcon(qta.icon("fa5s.clock", color="#5850EC"))

        self.timeline.insertItem(0, item)
        if self.timeline.count() > 20:
            self.timeline.takeItem(self.timeline.count() - 1)
