"""
agent2/sockets.py
─────────────────
All Socket.IO event handlers.
Call register_sockets(socketio) from main.py.
"""

import threading

from flask import request
from flask_socketio import emit, join_room

from agent2.config import (
    OS_NAME, SHELL_LABEL,
    MODELS, MODES, DEFAULT_MODEL, DEFAULT_MODE,
)
from agent2.database import qone, exe
from agent2.agent import run_agent, save_msg
from agent2.terminal import (
    stream_command, send_stdin, kill_proc,
    stop_agent, cleanup_sid,
)


def register_sockets(socketio) -> None:
    """Attach all socket.io event handlers to *socketio*."""

    # ── Connection lifecycle ──────────────────────────────────────────────────

    @socketio.on("connect")
    def on_connect():
        join_room(request.sid)
        emit("connected", {
            "sid":           request.sid,
            "os":            OS_NAME,
            "shell":         SHELL_LABEL,
            "models":        MODELS,
            "modes":         MODES,
            "default_model": DEFAULT_MODEL,
            "default_mode":  DEFAULT_MODE,
        })

    @socketio.on("disconnect")
    def on_disconnect():
        cleanup_sid(request.sid)

    # ── Chat messages ─────────────────────────────────────────────────────────

    @socketio.on("chat_message")
    def on_chat(data):
        sid = request.sid
        threading.Thread(
            target=run_agent,
            args=(
                data.get("chat_id"),
                data.get("message", "").strip(),
                sid,
                data.get("term_id", "t1"),
                data.get("model", DEFAULT_MODEL),
                data.get("mode",  DEFAULT_MODE),
                socketio,
                data.get("attachments", []),
            ),
            daemon=True,
        ).start()

    # ── Stop running agent ────────────────────────────────────────────────────

    @socketio.on("stop_agent")
    def on_stop_agent(_data):
        stop_agent(request.sid)
        emit("agent_stopped", {})

    # ── Edit a past user message (truncate + re-run) ──────────────────────────

    @socketio.on("edit_message")
    def on_edit_message(data):
        sid       = request.sid
        msg_id    = data.get("message_id")
        new_text  = data.get("new_text", "").strip()
        chat_id   = data.get("chat_id")
        term_id   = data.get("term_id",  "t1")
        model_key = data.get("model", DEFAULT_MODEL)
        mode_key  = data.get("mode",  DEFAULT_MODE)

        if not (msg_id and new_text and chat_id):
            return

        row = qone("SELECT created_at FROM messages WHERE id=?", (msg_id,))
        if not row:
            return

        # Delete the edited message and everything that came after it
        exe(
            "DELETE FROM messages WHERE chat_id=? AND created_at >= ?",
            (chat_id, row["created_at"]),
        )

        # Tell the UI to reload messages for this chat
        emit("messages_truncated", {"chat_id": chat_id, "from_msg_id": msg_id})

        # Re-run the agent with the new text
        threading.Thread(
            target=run_agent,
            args=(chat_id, new_text, sid, term_id, model_key, mode_key, socketio, []),
            daemon=True,
        ).start()

    # ── Terminal: run a raw command (no AI) ───────────────────────────────────

    @socketio.on("run_raw_command")
    def on_raw(data):
        sid     = request.sid
        cmd     = data.get("command", "").strip()
        term_id = data.get("term_id", "t1")
        if cmd:
            threading.Thread(
                target=stream_command,
                args=(cmd, sid, term_id, socketio),
                daemon=True,
            ).start()

    # ── Terminal: inject stdin into a running process ─────────────────────────

    @socketio.on("terminal_input")
    def on_stdin(data):
        sid     = request.sid
        term_id = data.get("term_id", "t1")
        text    = data.get("text", "")
        send_stdin(sid, term_id, text, socketio)

    # ── Terminal: kill running process ────────────────────────────────────────

    @socketio.on("terminal_kill")
    def on_kill(data):
        kill_proc(request.sid, data.get("term_id", "t1"))