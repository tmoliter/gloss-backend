from typing import List


def get_general_instructions(language_name: str):
    return f"""
You are a fluent {language_name} speaker, engaging with a visitor who is a learner of {language_name}. You do not know any other languages, and you only speak in {language_name}. Because you are engaging with a learner of {language_name}, you speak in terms that an intermediate learner might understand.

If the visitor uses any language aside from {language_name}, remind them IN {language_name.upper()} that you only know {language_name}. YOU MAY NOT USE ANY LANGUAGE OTHER THAN {language_name.upper()}.

If the visitor is ever confused, or seems to not make sense, try rephrasing what you said. Don't correct ALL grammar mistakes, but feel free to sometimes correct grammar mistakes as you see fit. This is not your primary purpose though, so avoid being egregious.

The first message that you receive should be completely ignored and you should ALWAYS respond with a greeting and introduction of who you are.
"""

def get_prompt(language: str, character_info: str, conversation_instructions: str, journal_words: List[str]):
    if language == "ja":
        language_name = "Japanese"
    elif language == "es":
        language_name = "Spanish"
    else:
        raise Exception("Unsupported language. Supported: 'es' (Spanish), 'ja' (Japanese)")

    general_instructions_section = get_general_instructions(language_name)

    character_info_section = f"""
** INFORMATION ABOUT WHO YOU ARE **

{character_info}

** END INFORMATION ABOUT WHO YOU ARE **

"""

    conversation_instructions_section = f"""
** CONVERSATION INSTRUCTIONS **

{conversation_instructions}

** END CONVERSATION INSTRUCTIONS **

"""
    
    if journal_words:
        journal_words_section = "Here are some words that the learner has recently studied in their journal. Try to use these words in your responses when appropriate:\n\n"
        for word in journal_words:
            journal_words_section += f"- {word}\n"
    else:
        journal_words_section = ""

    return f"""
{general_instructions_section}

{character_info_section}

{conversation_instructions_section}

{journal_words_section}

"""