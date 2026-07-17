"""
Chatbot route — menu-driven chatbot UI with session tracking.
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required
from app.services.chatbot_service import ChatbotService

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')
_bot = ChatbotService()


@chatbot_bp.route('/')
@login_required
def index():
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(id(session))  # Unique per session
    return render_template('chatbot/chat.html')


@chatbot_bp.route('/api/message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json(force=True)
    if not data or not data.get('message', '').strip():
        return jsonify({'success': False, 'response': 'Please send a message.'}), 400

    msg = data['message'].strip()
    sid = session.get('chat_session_id', 'default')

    result = _bot.process_message(msg, session_id=sid)
    history = session.get('chat_history', [])
    history.append({'role': 'user', 'message': msg})
    history.append({'role': 'bot', 'message': result['response'], 'type': result.get('type', 'answer')})
    session['chat_history'] = history[-30:]
    session.modified = True

    return jsonify({
        'success': True,
        'response': result['response'],
        'type': result.get('type', 'answer')
    })


@chatbot_bp.route('/api/clear', methods=['POST'])
@login_required
def clear_history():
    session['chat_history'] = []
    session['chat_session_id'] = str(id(session))
    if hasattr(_bot, 'user_sessions') and session.get('chat_session_id') in _bot.user_sessions:
        del _bot.user_sessions[session['chat_session_id']]
    session.modified = True
    return jsonify({'success': True})


@chatbot_bp.route('/api/history')
@login_required
def get_history():
    return jsonify({'success': True, 'history': session.get('chat_history', [])})
