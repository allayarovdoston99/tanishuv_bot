from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Ro'yxatdan o'tish holatlari"""
    choose_mode = State()
    input_name = State()
    input_birth_year = State()
    input_gender = State()
    input_city = State()
    input_photo = State()
    input_bio = State()
    
    # Nikoh rejimi uchun
    nikoh_religion = State()
    nikoh_occupation = State()
    nikoh_education = State()
    nikoh_marital_status = State()
    nikoh_children = State()
    
    # Do'st rejimi uchun
    dost_interests = State()
    dost_languages = State()
    
    # Talaba rejimi uchun
    talaba_university = State()
    talaba_faculty = State()
    talaba_course = State()
    
    # Qidiruv parametrlari
    search_gender = State()
    search_age_min = State()
    search_age_max = State()
    search_distance = State()
    
    confirm_rules = State()


class ProfileStates(StatesGroup):
    """Profil tahrirlash holatlari"""
    editing_name = State()
    editing_bio = State()
    editing_photo = State()
    editing_city = State()


class ChatStates(StatesGroup):
    """Suhbat holatlari"""
    in_chat = State()
    report_reason = State()
    report_details = State()


class AdminStates(StatesGroup):
    """Admin holatlari"""
    broadcast_message = State()
    ban_reason = State()
    view_user = State()


class StoryStates(StatesGroup):
    """Hikoya yuklash holatlari"""
    upload_story = State()       # foydalanuvchi rasm/video yuboradi
    add_caption = State()        # foydalanuvchi matn (caption) qo‘shadi
    confirm_story = State()      # foydalanuvchi tasdiqlaydi
    viewing_stories = State()    # hikoyalarni ko'rish holati


class GiftStates(StatesGroup):
    """Sovg'a yuborish holatlari"""
    choose_recipient = State()   # kimga sovg'a yuborishni tanlash
    choose_gift = State()        # sovg'a turini tanlash
    add_message = State()        # sovg'aga matn qo'shish
    confirm_gift = State()       # sovg'ani tasdiqlash


class IcebreakerStates(StatesGroup):
    """Suhbatni boshlash (icebreaker) holatlari"""
    choose_category = State()    # kategoriya tanlash
    show_question = State()      # savol/jumla ko‘rsatish
    answer_question = State()    # foydalanuvchi javob beradi
    confirm_use = State()        # tasdiqlash yoki keyingisini tanlash
    playing_game = State()       # o‘yin jarayonida bo‘lish holati

