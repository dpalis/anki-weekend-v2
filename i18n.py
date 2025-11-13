"""
Internationalization (i18n) for Weekend Addon
Detects Anki language and provides translations for PT-BR and EN.
"""

from aqt import mw

# Translations dictionary
TRANSLATIONS = {
    'pt_BR': {
        # Menu
        'menu_title': 'Weekend Addon',
        'menu_weekend_mode': 'Modo Fim de Semana',
        'menu_travel_mode': 'Modo Viagem',
        'menu_status': 'Ver Status',
        'menu_reset': 'Resetar Limites Armazenados',

        # Weekend mode messages
        'weekend_enabled': '📅 Modo Fim de Semana ATIVADO\n\nNovos cards serão pausados automaticamente aos finais de semana.\nDurante a semana, novos cards estarão ativos.',
        'weekend_disabled': '📅 Modo Fim de Semana DESATIVADO\n\nNovos cards permanecerão com seus limites normais todos os dias.\nO addon não fará nenhuma modificação automática.',

        # Travel mode messages
        'travel_enabled': '✈️ Modo Viagem ATIVADO\n\nNovos cards estão pausados.\nEles permanecerão pausados até você desativar o Modo Viagem.',
        'travel_disabled': '✈️ Modo Viagem DESATIVADO\n\nNovos cards serão retomados de acordo com o dia:\n• Fins de semana: Pausados\n• Dias de semana: Ativos',

        # Status dialog
        'status_title': 'Status do Weekend Addon',
        'status_today': '<b>Hoje:</b> {}',
        'status_travel_mode': '<b>Modo Viagem:</b> {}',
        'status_current_mode': '<b>Modo Atual:</b> {}',
        'status_behavior': '<b>Comportamento:</b>',
        'status_paused_travel': '• Novos cards estão <b>pausados</b> (Modo Viagem)',
        'status_paused_weekend': '• Novos cards estão <b>pausados</b> (Fim de semana)',
        'status_active_weekday': '• Novos cards estão <b>ativos</b> (Dia de semana)',
        'status_stored_limits': '<b>Limites Armazenados:</b> {} deck(s)',
        'status_tip': '<i>Dica: Use "Alternar Modo Viagem" para pausar/retomar novos cards manualmente.</i>',
        'status_enabled': '✅ Ativado',
        'status_disabled': '❌ Desativado',

        # Reset dialog
        'reset_title': 'Resetar Limites Armazenados',
        'reset_message': 'Isso limpará todos os limites originais armazenados.\n\nO addon recapturará seus limites atuais na próxima vez que pausar/retomar cards.\n\nContinuar?',
        'reset_success': '✅ Limites armazenados limpos!\n\nO addon recapturará seus limites atuais na próxima transição fim de semana/dia de semana.',
        'reset_error': 'Erro ao limpar limites: {}',

        # Days of week
        'monday': 'Segunda-feira',
        'tuesday': 'Terça-feira',
        'wednesday': 'Quarta-feira',
        'thursday': 'Quinta-feira',
        'friday': 'Sexta-feira',
        'saturday': 'Sábado',
        'sunday': 'Domingo',

        # Common
        'please_open_profile': 'Por favor, abra um perfil primeiro.',

        # Mode names
        'mode_weekday': 'Dia de semana',
        'mode_weekend': 'Fim de semana',
        'mode_travel': 'Viagem',
        'mode_unknown': 'Ainda não aplicado',
    },
    'en': {
        # Menu
        'menu_title': 'Weekend Addon',
        'menu_weekend_mode': 'Weekend Mode',
        'menu_travel_mode': 'Travel Mode',
        'menu_status': 'View Status',
        'menu_reset': 'Reset Stored Limits',

        # Weekend mode messages
        'weekend_enabled': '📅 Weekend Mode ENABLED\n\nNew cards will be automatically paused on weekends.\nDuring weekdays, new cards will be active.',
        'weekend_disabled': '📅 Weekend Mode DISABLED\n\nNew cards will keep their normal limits every day.\nThe addon will not make any automatic modifications.',

        # Travel mode messages
        'travel_enabled': '✈️ Travel Mode ENABLED\n\nNew cards are now paused.\nThey will remain paused until you disable Travel Mode.',
        'travel_disabled': '✈️ Travel Mode DISABLED\n\nNew cards will resume according to the day:\n• Weekends: Paused\n• Weekdays: Active',

        # Status dialog
        'status_title': 'Weekend Addon Status',
        'status_today': '<b>Today:</b> {}',
        'status_travel_mode': '<b>Travel Mode:</b> {}',
        'status_current_mode': '<b>Current Mode:</b> {}',
        'status_behavior': '<b>Behavior:</b>',
        'status_paused_travel': '• New cards are <b>paused</b> (Travel Mode)',
        'status_paused_weekend': '• New cards are <b>paused</b> (Weekend)',
        'status_active_weekday': '• New cards are <b>active</b> (Weekday)',
        'status_stored_limits': '<b>Stored Limits:</b> {} deck(s)',
        'status_tip': '<i>Tip: Use "Toggle Travel Mode" to pause/resume new cards manually.</i>',
        'status_enabled': '✅ Enabled',
        'status_disabled': '❌ Disabled',

        # Reset dialog
        'reset_title': 'Reset Stored Limits',
        'reset_message': 'This will clear all stored original limits.\n\nThe addon will recapture your current limits the next time it pauses/resumes cards.\n\nContinue?',
        'reset_success': '✅ Stored limits cleared!\n\nThe addon will recapture your current limits on the next weekend/weekday transition.',
        'reset_error': 'Error clearing limits: {}',

        # Days of week
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday',

        # Common
        'please_open_profile': 'Please open a profile first.',

        # Mode names
        'mode_weekday': 'Weekday',
        'mode_weekend': 'Weekend',
        'mode_travel': 'Travel',
        'mode_unknown': 'Not yet applied',
    }
}


def detect_language() -> str:
    """
    Detect Anki's language setting.

    Returns:
        'pt_BR' for Portuguese (Brazil), 'en' for English (default)
    """
    if not mw:
        return 'en'

    try:
        # Try multiple methods to detect language
        lang = None

        # Primary method: Check Anki's current language (Anki 25.x)
        try:
            from anki.lang import current_lang
            lang = current_lang
        except Exception:
            pass

        # Fallback 1: Check profile manager meta
        if not lang and mw.pm:
            lang = mw.pm.meta.get('lang')

        # Fallback 2: Check collection config
        if not lang and mw.col:
            try:
                lang = mw.col.get_config('lang')
            except Exception:
                pass

        # Map language codes to our supported languages
        if lang and lang.lower().startswith('pt'):  # pt, pt_BR, pt-BR, pt_PT
            return 'pt_BR'
        else:
            return 'en'  # Default to English
    except Exception:
        return 'en'


def tr(key: str) -> str:
    """
    Translate a key to the current language.

    Args:
        key: Translation key

    Returns:
        Translated string, or key if translation not found
    """
    lang = detect_language()

    try:
        return TRANSLATIONS[lang][key]
    except KeyError:
        # Fallback to English if translation not found
        try:
            return TRANSLATIONS['en'][key]
        except KeyError:
            # Return key if not found in any language
            return key
