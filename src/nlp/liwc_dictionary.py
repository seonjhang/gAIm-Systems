# Full LIWC Dictionary based on LIWC2015
# Comprehensive categories for psychological and linguistic analysis

LIWC_CATEGORIES = {
    # Linguistic Dimensions
    'first_person_singular': ['i', 'me', 'my', 'myself', 'mine'],
    'first_person_plural': ['we', 'us', 'our', 'ours', 'ourselves'],
    'second_person': ['you', 'your', 'yours', 'yourself', 'yourselves', "you're", "you've", "you'd"],
    'third_person': ['he', 'she', 'they', 'him', 'her', 'them', 'his', 'their', 'hers'],
    
    # Grammatical
    'articles': ['a', 'an', 'the'],
    'prepositions': ['in', 'on', 'at', 'for', 'with', 'by', 'from', 'to', 'of', 'about', 'into', 'onto', 'over', 'after', 'before', 'until', 'during', 'through', 'across', 'against', 'toward', 'within', 'without', 'behind', 'beyond', 'among', 'between', 'beside', 'beneath', 'below', 'under'],
    'auxiliary_verbs': ['am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'must', 'can', 'may', 'might'],
    'adverbs': ['very', 'really', 'quite', 'rather', 'too', 'so', 'just', 'only', 'even', 'still', 'also', 'however', 'therefore', 'thus', 'hence', 'consequently', 'moreover', 'furthermore', 'additionally'],
    'conjunctions': ['and', 'or', 'but', 'nor', 'yet', 'so', 'because', 'since', 'if', 'unless', 'although', 'though', 'whereas', 'while'],
    'negations': ['no', 'not', 'never', 'none', 'nobody', 'nothing', 'nowhere', 'neither', 'nor', "can't", "won't", "don't", "didn't", "couldn't", "shouldn't", "wouldn't", "isn't", "wasn't", "aren't", "weren't", "haven't", "hasn't", "hadn't"],
    'numbers': ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'hundred', 'thousand', 'million', 'first', 'second', 'third', 'fourth', 'fifth'],
    
    # Emotional Processes
    'positive_emotion': ['happy', 'joy', 'love', 'laugh', 'smile', 'great', 'good', 'excellent', 'awesome', 'fantastic', 'wonderful', 'amazing', 'beautiful', 'brilliant', 'celebrate', 'cheerful', 'delighted', 'ecstatic', 'glad', 'grateful', 'pleased', 'proud', 'thrilled', 'enjoy', 'enjoyable', 'fun', 'funny', 'humor', 'laughter', 'liked', 'loved', 'optimism', 'optimistic'],
    'negative_emotion': ['sad', 'angry', 'hate', 'fear', 'worry', 'anxiety', 'stress', 'bad', 'terrible', 'awful', 'frustrated', 'upset', 'disappointed', 'hopeless', 'hurt', 'hurtful', 'lonely', 'melancholy', 'miserable', 'regret', 'sorry', 'unhappy', 'disgusted', 'horrible'],
    'anxiety': ['worried', 'anxious', 'nervous', 'afraid', 'fear', 'panic', 'stress', 'pressure', 'tension', 'fearful', 'frightened', 'scared', 'horror', 'terrified', 'apprehensive', 'concern', 'concerned'],
    'anger': ['angry', 'mad', 'frustrated', 'annoyed', 'annoying', 'fury', 'furious', 'irritated', 'outrage', 'rage', 'upset', 'hate', 'hatred', 'hostile'],
    'sadness': ['sad', 'depressed', 'depressing', 'sorrow', 'sorrowful', 'grief', 'grieving', 'tears', 'crying', 'weep', 'weeping', 'mourn', 'mourning'],
    
    # Cognitive Processes
    'insight': ['think', 'thought', 'know', 'understand', 'realize', 'consider', 'consideration', 'aware', 'awareness', 'conscious', 'contemplate', 'examine', 'mind', 'minds', 'perceive', 'reason', 'reflect', 'speculate', 'thinking'],
    'cause': ['because', 'effect', 'reason', 'why', 'since', 'therefore', 'due', 'caused', 'causes', 'consequently', 'result', 'results', 'resulting'],
    'certainty': ['always', 'never', 'definitely', 'certain', 'sure', 'absolute', 'absolutely', 'certainly', 'clear', 'clearly', 'convinced', 'doubtless', 'guaranteed', 'guarantee', 'obvious', 'obviously', 'positive', 'positively', 'precise', 'precisely'],
    'doubt': ['maybe', 'perhaps', 'might', 'could', 'uncertain', 'unsure', 'unclear', 'confused', 'confusion', 'doubt', 'doubtful', 'guess', 'hesitant', 'hesitate', 'possibly', 'probably', 'question', 'questionable', 'uncertainty', 'wonder'],
    'discrepancy': ['but', 'except', 'however', 'if', 'instead', 'rather', 'should', 'though', 'unless', 'whereas', 'wish', 'would', 'could'],
    'tentative': ['maybe', 'perhaps', 'might', 'probably', 'seem', 'seems', 'somewhat', 'tend', 'tends', 'uncertain', 'apparently', 'appears', 'appeared'],
    'differentiation': ['alternative', 'alternatively', 'but', 'contrast', 'different', 'differentiate', 'either', 'else', 'except', 'however', 'instead', 'other', 'others', 'otherwise', 'rather', 'than', 'though', 'versus', 'whereas'],
    
    # Social Processes
    'family': ['mother', 'father', 'mom', 'dad', 'parent', 'parents', 'brother', 'sister', 'son', 'daughter', 'children', 'child', 'family', 'families', 'grandmother', 'grandfather', 'uncle', 'aunt', 'cousin', 'nephew', 'niece'],
    'friend': ['friend', 'friends', 'buddy', 'buddies', 'pal', 'pals', 'teammate', 'teammates', 'colleague', 'colleagues', 'companion', 'companions', 'peer', 'peers'],
    'humans': ['boy', 'girl', 'man', 'woman', 'men', 'women', 'person', 'people', 'persons', 'human', 'humans', 'guy', 'guys', 'individual', 'individuals'],
    
    # Biological Processes
    'health': ['healthy', 'health', 'illness', 'ill', 'sick', 'disease', 'medical', 'medicine', 'doctor', 'hospital', 'treatment', 'therapy', 'pain', 'ache', 'healing'],
    'sexual': ['sexy', 'sex', 'sexual', 'romantic', 'romance', 'dating', 'date', 'kiss', 'kissed', 'passion', 'passionate'],
    'ingestion': ['eat', 'eating', 'ate', 'food', 'meal', 'meals', 'drink', 'drinking', 'drank', 'dining', 'feast', 'hungry', 'hunger', 'thirsty'],
    
    # Perceptual Processes
    'see': ['see', 'saw', 'seen', 'seeing', 'vision', 'visual', 'view', 'views', 'viewing', 'watch', 'watched', 'watching', 'look', 'looked', 'looking', 'observe', 'observed', 'observing', 'perceive', 'perceived', 'glimpse', 'glance', 'stare', 'staring', 'notice', 'noticed'],
    'hear': ['hear', 'heard', 'hearing', 'listen', 'listening', 'listened', 'sound', 'sounds', 'silent', 'silence', 'volume', 'audio', 'audible', 'voice', 'voices'],
    'feel': ['feel', 'feels', 'felt', 'feeling', 'touch', 'touched', 'touching', 'texture', 'sensation', 'sense', 'sensing'],
    
    # Personal Concerns
    'work': ['work', 'worked', 'working', 'works', 'job', 'jobs', 'office', 'career', 'business', 'employer', 'employee', 'boss', 'manager', 'task', 'tasks', 'project', 'projects', 'deadline', 'deadlines', 'meeting', 'meetings', 'conference'],
    'achievement': ['achieve', 'achieved', 'achievement', 'success', 'successful', 'accomplish', 'accomplished', 'goal', 'goals', 'win', 'won', 'winning', 'wins', 'victory', 'victories', 'champion', 'championship', 'earn', 'earned', 'master', 'mastery', 'competition'],
    'leisure': ['leisure', 'hobby', 'hobbies', 'fun', 'entertainment', 'play', 'played', 'playing', 'game', 'games', 'gaming', 'relax', 'relaxing', 'vacation', 'holiday', 'break', 'rest', 'relaxation'],
    'home': ['home', 'house', 'household', 'apartment', 'room', 'rooms', 'bedroom', 'kitchen', 'living', 'bathroom', 'door', 'doors', 'window', 'windows'],
    'money': ['money', 'dollar', 'dollars', 'cash', 'pay', 'paid', 'payment', 'salary', 'wage', 'wages', 'income', 'afford', 'expensive', 'cheap', 'buy', 'bought', 'buying', 'sell', 'sold', 'selling', 'price', 'prices', 'cost', 'costs'],
    'religion': ['god', 'gods', 'church', 'religious', 'religion', 'faith', 'faithful', 'pray', 'prayed', 'praying', 'prayer', 'divine', 'heaven', 'hell', 'angel', 'angels', 'soul', 'souls', 'spiritual', 'spirit'],
    'death': ['death', 'dead', 'die', 'died', 'dying', 'dies', 'kill', 'killed', 'killing', 'kills', 'suicide', 'murder', 'funeral', 'cemetery', 'grave', 'graveyard', 'burial'],
    
    # Informal Language
    'swear_words': ['damn', 'hell', 'sh*t', 'f*ck', 'f*cking', 'b*th', 'a*s', 'a*shole', 'ba*tard', 'cr*p', 'freaking'],
    'assent': ['ok', 'okay', 'yes', 'yeah', 'yep', 'yup', 'sure', 'alright', 'right', 'uhuh'],
    'nonfluencies': ['er', 'erm', 'uh', 'um', 'hmm', 'hm', 'ah', 'eh', 'oh', 'well', 'you know', 'i mean', 'like', 'kinda', 'sorta'],
    
    # Tense Markers (for draft prediction analysis)
    'past_tense': ['was', 'were', 'did', 'had', 'went', 'said', 'told', 'got', 'came', 'saw', 'took', 'made', 'gave', 'knew', 'thought', 'felt', 'tried', 'found', 'became', 'started', 'ran', 'played', 'won', 'lost', 'scored', 'scored'],
    'present_tense': ['am', 'is', 'are', 'do', 'does', 'have', 'has', 'say', 'go', 'come', 'see', 'take', 'make', 'give', 'know', 'think', 'feel', 'try', 'find', 'become', 'start', 'run', 'play', 'win', 'score'],
    'future_tense': ['will', 'would', 'shall', 'should', 'going to', 'gonna', 'about to', 'plan to', 'intend to', 'hope to', 'expect to', 'look forward to', 'aim to'],
    
    # Draft/Sports-Specific Categories
    'competition': ['compete', 'competing', 'competition', 'competitor', 'opponent', 'rival', 'rivalry', 'game', 'games', 'match', 'matches', 'tournament', 'championship', 'playoff', 'playoffs', 'finals', 'beat', 'beating', 'win', 'winning', 'lose', 'losing', 'defeat', 'victory', 'battle'],
    'training': ['practice', 'practicing', 'practiced', 'training', 'train', 'trained', 'drill', 'drills', 'workout', 'workouts', 'exercise', 'conditioning', 'preparation', 'preparing', 'prepare', 'rehearse', 'rehearsal'],
    'performance': ['performance', 'perform', 'performed', 'performing', 'execution', 'execute', 'executed', 'skill', 'skills', 'ability', 'abilities', 'talent', 'talented', 'technique', 'techniques'],
    'goal_orientation': ['goal', 'goals', 'target', 'targets', 'objective', 'objectives', 'aim', 'aims', 'purpose', 'pursuit', 'pursue', 'pursuing', 'strive', 'striving', 'aspire', 'aspiring'],
    'confidence': ['confident', 'confidence', 'believe', 'believes', 'sure', 'certain', 'definitely', 'absolutely', 'certainly', 'doubtless', 'trust', 'positive', 'optimistic', 'optimism'],
    'determination': ['determined', 'determination', 'committed', 'commitment', 'dedicated', 'dedication', 'perseverance', 'persevere', 'persist', 'persistence', 'persistent', 'resolve', 'resolute', 'focused', 'focus'],
    'leadership': ['lead', 'leadership', 'leader', 'leaders', 'leading', 'led', 'captain', 'captains', 'captaincy', 'lead by example', 'role model', 'mentor', 'mentoring', 'guide', 'guiding'],
    'team_orientation': ['team', 'teams', 'teammate', 'teammates', 'together', 'cooperation', 'cooperate', 'collaboration', 'collaborate', 'united', 'unity', 'together', 'collective', 'partnership', 'squad'],
    'individual_focus': ['individual', 'individually', 'alone', 'myself', 'solo', 'independent', 'independence', 'self-reliant', 'personal', 'personally'],
    'physical': ['strength', 'strong', 'stronger', 'power', 'powerful', 'speed', 'fast', 'faster', 'quick', 'quicker', 'agility', 'agile', 'endurance', 'stamina', 'athletic', 'athlete', 'athletes'],
    'pressure': ['pressure', 'pressures', 'stress', 'stressed', 'nervous', 'nervousness', 'anxious', 'anxiety', 'tense', 'tension', 'strain', 'burden', 'demanding', 'challenge', 'challenging'],
    'future_planning': ['future', 'futures', 'next', 'soon', 'upcoming', 'ahead', 'forward', 'plans', 'planning', 'strategy', 'strategies', 'roadmap', 'vision', 'opportunity', 'opportunities'],
    'experience': ['experience', 'experiences', 'experienced', 'learn', 'learned', 'learning', 'learns', 'knowledge', 'know-how', 'expertise', 'wisdom', 'understanding', 'insights', 'lessons'],
    
    # Additional Advanced Predictors for Draft Success
    'accountability': ['responsible', 'responsibility', 'accountable', 'accountability', 'blame', 'fault', 'mistake', 'mistakes', 'error', 'errors', 'own', 'owned'],
    'process_focus': ['process', 'practice', 'practicing', 'practiced', 'work', 'working', 'worked', 'effort', 'efforts', 'hard work', 'improve', 'improving', 'improvement', 'steps', 'step by step'],
    'outcome_focus': ['win', 'winning', 'championship', 'championships', 'title', 'titles', 'trophy', 'trophies', 'result', 'results', 'score', 'scores', 'scored', 'final', 'finals'],
    'growth_mindset': ['improve', 'improving', 'improvement', 'grow', 'growing', 'growth', 'develop', 'developing', 'development', 'progress', 'progressing', 'better', 'get better', 'potential'],
    'self_awareness': ['reflect', 'reflecting', 'reflection', 'reflects', 'analyze', 'analysis', 'understand', 'understand myself', 'strengths', 'weaknesses', 'strength', 'weakness', 'honest', 'honesty'],
    'accountability_avoidance': ['blame', 'blamed', 'blaming', 'excuse', 'excuses', 'fault', 'faults', "wasn't my fault", "not my fault", 'unfortunate', 'bad luck', 'unlucky'],
    'gratitude': ['thankful', 'thanks', 'appreciate', 'appreciation', 'grateful', 'gratitude', 'blessed', 'fortunate', 'privilege', 'privileged'],
    'comparison_to_others': ['compared to', 'like him', 'like her', 'like them', 'better than', 'worse than', 'compared', 'comparison', 'similar to', 'different from'],
    'resilience': ['bounce back', 'come back', 'recover', 'recovery', 'resilient', 'persevere', 'perseverance', 'overcome', 'overcame', 'fight', 'fighting', 'never give up', 'keep going'],
    'coachability': ['listen', 'listening', 'feedback', 'advice', 'advise', 'guidance', 'teachable', 'coachable', 'open to', 'receptive', 'willing to learn', 'learn from'],
    'decision_making': ['decide', 'decided', 'decision', 'decisions', 'choose', 'chosen', 'choice', 'choices', 'strategic', 'strategy', 'plan', 'planned', 'planning'],
    'adaptability': ['adapt', 'adapting', 'adaptation', 'adjust', 'adjusting', 'adjustment', 'flexible', 'flexibility', 'versatile', 'versatility', 'change', 'changing', 'situational'],
    'negative_self_talk': ["can't", 'cannot', "won't", "don't", "couldn't", 'unable', 'impossible', 'hopeless', 'useless', 'worthless']
}

