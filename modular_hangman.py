class Messenger:
    def __init__(self, reply_array, **kwargs):
        self.reply_array = reply_array                  # Stores the reply array
        self.join_user = kwargs.get("join_users")       # Stores user id joining
        self.unjoin_user = kwargs.get("unjoin_users")   # Stores user id quitting

class Hangman:
    """
    Modularly designed Hangman class definition.
    
    This class is a Hangman game designed with modularity in mind. It's actually an
    adaptation from the Hangman LINE bot. This class methods mostly return reply array
    consisting of text string of replies, instead of directly interacting with the 
    LINE Messaging API. That way, a Mastermind-type class can be created to be the 
    base foundation of the program, housing the games and memberships dictionary.
    
    REVISION: This class methods will return a Messenger object (actually a simple
    class to syntactically sugar a dictionary) that contains reply array along with
    other requests that ensue, e.g. join or unjoin a player.
    
    NOTE: This meeans the Mastermind of the Messaging API needs to process the
    reply array before actually sending the message, since this class has no way
    to know TextSendMessage class exists.
    """
    
    # KEYWORDS USED IN-GAME

    keyword_start_game = "/start"
    keyword_join = "/join"
    keyword_unjoin = "/quit"
    keyword_end = "/end"
    keyword_scoreboard = "/scoreboard"
    keyword_history = "/history"
    keyword_continue_game = "/continue"
    keyword_show = "/show"
    keyword_add_word = "/add"
    
    def __init__(self, score_per_letter, score_per_word):
        self.score_per_letter = score_per_letter
        self.score_per_word = score_per_word    
        self.active_word = ""              # Active word in play
        self.waiting_list = []             # Words in waiting list
        self.show_string = ""              # Shown string. H_NGM_N
        self.letter_states = {}            # States of each letter. Is it guessed?
        self.participants = {}             # Participant dictionary. Storing user_id and display_name at join.
                                           # NOTE TO SELF: WHAT IF SOMEONE /ADD THEN /QUIT?
                                           # "Player is not in game anymore."
        self.scoreboard = [[],[]]          # Table of participant and score. List of lists to preserve ordering.
        self.history = [[],[],[],[]]       # History of who guesses what for how much score, and what word was in play.
        
        """
        Sources, or givers, are not implemented in list of list style
        to minimize interruptions and edits that go with its introduction/implementation
        """
        self.waiting_source = []           # The giver of each word in the waiting list
        self.active_word_source = ""       # The giver of the currently active word
        
        self.paused = True                 # Pause system. Introduced to combat /continue bug
    
    def include_participant(self, user_id, display_name):
        """
        Include participant with user_id and using display_name
        as name used in the currently running game joined.
        
        Return a message.
        """
        reply_array = []
        join_user = None
        if user_id not in self.participants:
            self.participants[user_id] = display_name
            if user_id not in self.scoreboard:
                self.scoreboard[0] += [user_id]
                self.scoreboard[1] += [0]
            reply_array.append(
                (display_name + " has joined. " +
                 "You can submit words privately by using " +
                 self.keyword_add_word + " YOURWORDHERE to " +
                 "the OA.")
            )
            join_user = user_id
        else:
            reply_array.append(
                self.participants.get(user_id) + " is already in play."
            )
        return Messenger(reply_array, join_user=join_user)
    
    def exclude_participant(self, user_id):
        """
        Remove participant with the specified user_id from play.
        """
        reply_array = []
        unjoin_user = None
        if user_id in self.participants:
            reply_array.append(
                self.participants.get(user_id) + " is removed from play."
            )
            del self.participants[user_id]
            unjoin_user = user_id
        else:
            reply_array.append(
                "Can't remove from play as you haven't joined."
            )
        return Messenger(reply_array, unjoin_user=unjoin_user)
    
    def show_participants(self):
        """
        Return reply array of one member, i.e. the participant list
        in a long string.
        """
        reply_array = []
        participants_chat = ""
        for i in self.participants:
            participants_chat += self.participants.get(i)
            participants_chat += "\n"
        reply_array.append(participants_chat)
        return Messenger(reply_array)
    
    def initiate_letter_states(self):  # For setting the letter states into all-false (no guessed letters) after a new word is given
        unique_letters = self.active_word.upper()
        unique_letters = list(set(list(unique_letters)))
        unique_letters = list(''.join(filter(str.isalpha, ''.join(unique_letters))))
        self.letter_states = {k: False for k in unique_letters}
    
    def update_show_string(self):
        """
        Update the show_string. Not return anything.
        """
        self.show_string = ""
        char_index = 0
        for char in self.active_word:
            if self.letter_states.get(char, True):
                # This way, punctuation and other nonalphabet character is 
                # always shown.
                self.show_string += char
            else:
                self.show_string += "_"
            self.show_string += " "          # Add space after each characters. Will improve readability.
    
    def show_banner(self):
        """
        Return a list of one member, the show_string.
        """
        return Messenger([self.show_string])
    
    def word_is_guessed(self):
        if all(self.letter_states.values()):
            return True
        else:
            return False
    
    def add_word(self, word, user_id):
        """
        Append the word and the user_id to the respective waiting lists.
        
        Will reply with rejection message if word added is a keyword.
        """
        reply_array = []
        if not self.paused:
            reply_array.append(
                ("Cannot submit word, " +
                 "game is not in paused state.")
            )
        elif ("/" + word in [self.keyword_help,
                             self.keyword_join,
                             self.keyword_unjoin,
                             self.keyword_scoreboard,
                             self.keyword_history,
                             self.keyword_continue_game,
                             self.keyword_show]):
            # word is a keyword.
            reply_array.append(
                ("Your proposed word is rejected " + 
                 "because it's a reserved keyword.")
            )
        elif len(word) < 5:
            # Word too short. Minimum 5 letters.
            reply_array.append(
                ("Your proposed word is rejected because it's too short.")
            )
        
        else:
            self.waiting_list.append(word)
            self.waiting_source.append(user_id)
            reply_array.append("Your proposed word is accepted.")
        
        return Messenger(reply_array)
    
    def fetch_word(self):
        """
        Take a word from waiting list.
        """
        self.active_word = self.waiting_list.pop(0).upper()
        self.active_word_source = self.waiting_source.pop(0)
        self.initiate_letter_states()
        self.update_show_string()
        
    
    def guess(self, user_id, letter):
        """
        Take a letter and user_id as input, and try to guess
        the word using such letter. Return reply array.
        """
        reply_array = []
        letter = letter.upper()
        if self.paused:
            reply_array.append(
                ("Game is now still paused." +
                 " Use " + self.keyword_continue_game +
                 " to continue the game.")
            )
        elif user_id == self.active_word_source:
            reply_array.append(
                ("You, " + self.participants.get(user_id) +
                 " are the giver of this word." +
                 " You can't guess it.")
            )
        elif self.word_is_guessed():
            reply_array.append("Word is already guessed.")
        elif letter in self.letter_states:
            if not self.letter_states[letter]:
                self.letter_states[letter] = True
                
                self.update_show_string()
                
                position = self.scoreboard[0].index(user_id)
                self.scoreboard[1][position] += self.score_per_letter
            
                self.history[0] += [user_id]
                self.history[1] += [letter]
                self.history[2] += [self.score_per_letter]
                self.history[3] += [self.show_string]                
            else:
                reply_array.append("Correct, but this letter is already guessed.")
        else:
            reply_array.append("No such letter (" + letter + ").")
        
        reply_array.append(self.show_string)
        
        if self.word_is_guessed():
            reply_array.append(self.get_scoreboard())
            if self.waiting_list:
                self.fetch_word()
                reply_array.append(
                    ("Guess this new word:\n" + self.show_string +
                     "\n\nSubmitted by: " + self.participants.get(self.active_word_source, "Player not in game anymore."))
                )
            else:
                self.paused = True
                reply_array.append(
                    ("Game is now paused." +
                     " There is no word left in the waiting list." +
                     " Please give word by using " + self.keyword_add_word +
                     " to the OA. Then use " + self.keyword_continue_game +
                     " here to continue the game.")
                )
        
        return Messenger(reply_array)
    
    def guess_word(self, user_id, word):
        """
        Take a word and user_id as input, and try to guess
        the word. Return reply array.
        """
        reply_array = []
        if self.paused:
            reply_array.append(
                ("Game is now still paused." +
                 " Use " + self.keyword_continue_game +
                 " to continue the game.")
            )
        elif user_id == self.active_word_source:
            reply_array.append(
                ("You, " + self.participants.get(user_id) +
                 " are the giver of this word." +
                 " You can't guess it.")
            )
        elif self.word_is_guessed():
            reply_array.append(TextSendMessage(text="Word is already guessed."))
        elif word.upper() == self.active_word.upper():
            """
            Caution: This if function requires the guess to be exact down to the punctuation.
            The guess can only vary in lower vs uppercase. Not including the punctuation makes the guess wrong.
            However, in single-letter guesses, punctuation is not necessary to be guessed to make the word complete.
            """
            user_position = self.scoreboard[0].index(user_id)
            self.scoreboard[1][user_position] += self.score_per_word
            letters_remaining = 0
            for letter in self.letter_states:
                if not self.letter_states[letter]:
                    self.letter_states[letter] = True
                    self.scoreboard[1][user_position] += self.score_per_letter
                    letters_remaining += 1
            
            self.update_show_string()
            
            self.history[0] += [user_id]
            self.history[1] += [word]
            self.history[2] += [self.score_per_word + letters_remaining*self.score_per_letter]
            self.history[3] += [self.show_string]
        else:
            reply_array.append(word + " is not the right word.")
        
        reply_array.append(self.show_string)
        
        if self.word_is_guessed():
            reply_array.append(self.get_scoreboard())
            if self.waiting_list:
                self.fetch_word()
                reply_array.append(
                    ("Guess this new word:\n" + self.show_string +
                     "\n\nSubmitted by: " + self.participants.get(self.active_word_source, "Player not in game anymore."))
                )
            else:
                self.paused = True
                reply_array.append(
                    ("Game is now paused." +
                     " There is no word left in the waiting list." +
                     " Please give word by using " + self.keyword_add_word +
                     " to the OA. Then use " + self.keyword_continue_game +
                     " here to continue the game.")
                )
        
        return Messenger(reply_array)
    
    def continue_game(self):
        """
        Continue game after being paused, i.e. when no words
        are left in the waiting list.
        """
        reply_array = []
        if not self.paused:
            reply_array.append("Game is not in paused state.")
        elif not self.waiting_list:
            reply_array.append(
                ("The waiting list is still empty." +
                 " Please give word by using " + self.keyword_add_word +
                 " to the OA. Then use " + self.keyword_continue_game +
                 " here to continue the game.")
            )
        else:
            self.fetch_word()
            reply_array.append(
                ("Game is now continued.\n" +
                 "Guess this new word:\n" + self.show_string +
                 "\n\nSubmitted by: " + self.get_name(self.active_word_source, "Player not in game anymore."))
            )
            self.paused = False
        
        return Messenger(reply_array)
    
    def sort_scoreboard(self):
        """
        Sort the scoreboard.
        """
        participants_sorted = [name for value, name in sorted(zip(self.scoreboard[1], self.scoreboard[0]), reverse=True)]
        score_sorted = sorted(self.scoreboard[1], reverse=True)
        self.scoreboard = [participants_sorted, score_sorted]
    
    def get_scoreboard(self):
        """
        Return the scoreboard as a long string.
        """
        self.sort_scoreboard()
        scoreboard_chat = "SCOREBOARD"
        for i in range(len(self.scoreboard[0])):
            scoreboard_chat += "\n"
            scoreboard_chat += str(self.get_name(self.scoreboard[0][i]))
            scoreboard_chat += ": "
            scoreboard_chat += str(self.scoreboard[1][i])
        return scoreboard_chat
    
    def show_scoreboard(self):
        """
        Return a reply array of one member, i.e.
        scoreboard, ready to be printed. Maintained
        for consistency.
        """
        return Messenger([self.get_scoreboard()])
    
    def show_history(self):
        """
        Return a reply array of one member, i.e.
        history. Implemented this way for consistency
        """
        history_chat = "HISTORY"
        length = len(self.history[0])
        # Is 20 last entries enough?
        for i in range(max(0, length-20), length):
            history_chat += "\n"
            history_chat += str(self.get_name(self.history[0][i]))
            history_chat += " | "
            history_chat += str(self.history[1][i])
            history_chat += " | "
            history_chat += str(self.history[2][i])
            history_chat += " | "
            history_chat += str(self.history[3][i])
        
        return Messenger([history_chat])
    
    def show_help(self):
        """
        Return a reply array of help for keywords for this game.
        """
        reply_array = []
        reply_array.append((
            "HANGMAN HELP" "\n"
            "1. WHAT IS HANGMAN?" "\n"
            "It is a game where you guess a word letter-per-letter. Each correct letter you guess will yield a score." "\n"
            "\n"
            "2. HOW DOES THIS BOT WORK?" "\n"
            "Invite this bot to a group. There, you can play Hangman with your friends. Send a single letter to guess that letter, and send a phrase prefixed with / to take a guess of the phrase entirely, e.g '/CONVEX HULL'" "\n"
            "\n"
            "3. WHERE DID THE WORDS COME FROM?" "\n"
            "The words come from players in the same game sending the word via private chat to OA." "\n"
            "\n"
        ))
        reply_array.append((
            "4. KEYWORDS?" "\n"
            "Below are keywords usable in communicating with the bot in playing this game:" "\n"
            "- '" + keyword_help + "' : display this help." "\n"
            "- '" + keyword_join + "' : join a game in a group." "\n"
            "- '" + keyword_unjoin + "' : quit a game in a group." "\n"
            "- '" + keyword_add_word + "' : add a word or phrase to be guessed. Send to OA with format '" + keyword_add_word + " YOUR PHRASE HERE'. Multi-word phrase is allowded."  "\n"
            "- '" + keyword_continue_game + "' : continue a paused game, after players have added words for the game." "\n"
            "- '" + keyword_scoreboard + "' : display the scoreboard in a game." "\n"
            "- '" + keyword_history + "' : display the history in a game up to last 20 correct guesses." "\n"
            "- '" + keyword_show + "' : show the phrase in the game, just in case it gets too buried and you need to show it again." "\n"
            "\n"
        ))
        reply_array.append((
            "5. HOW DOES THE SCORING WORK?" "\n"
            "1 score for each correct letter guessed. When guessing entire phrase at once, the score given is how many letters un-guessed are remaining, plus extra 10 score." "\n"
            "\n"
            "6. MISCELLANEOUS" "\n"
            "- You can customize the scoring when starting the game. Instead of saying '" + keyword_add_game + "', say '" + keyword_add_game + " 2 50' to change the scoring for 2 per letter and 50 extra per phrase. This can only be done when starting the game. The scoring can't be changed mid-game." "\n"
            "- Guessing the entire phrase at once requires you to be precise." "\n"
            "- Your name will remain in the scoreboard once you join the game, even when you quit the game."
        ))
        return Messenger(reply_array)
        
    def show_report_status(self):
        # Report game status/progress.
        # How many words are waiting, how many words have been played, etc.
        # Currently not bound to a keyword.
        report_chat = ""
        report_chat += ("Waiting list: " + str(len(self.waiting_list)) + "\n")
        report_chat += ("Players: " + str(len(self.participants)) + "\n")
        return Messenger([report_chat])
    
    def show_hello(self):
        start_chat = ("Welcome! A Hangman game is now started. " +
                      "Join by saying " + self.keyword_join +
                      " now!")
        
        return Messenger([start_chat])
    
    def show_goodbye(self):
        # Can be used to terminate a game before remove_game() is then called.
        # NOT USED.
        reply_array = []
        end_chat = ("Thank you for playing this game!" + 
                     " Now the game will be terminated.")
        reply_array.append(self.get_scoreboard)
        reply_array.append(end_chat)
        return Messenger(reply_array)
    
    def parse_and_reply(self, channel, received_text, user_id, display_name, group_id):
        # Series of if else clauses to determine which method to invoke.
        # The Mastermind will link a user with its group, then its group
        # with its game; using the games and memberships dictionary. This
        # method lies as first act of response of the said game.
        # NOTE TO SELF: HOW CAN THEN THE GAMES AND MEMBERSHIPS DICTIONARY
        # BE UPDATED IF THE PARSING IS DONE ON CLASS LEVEL?
        # NOTE TO SELF II: LET MASTERMIND KNOW USED KEYWORDS?
        # The notion of Hangman class passing resulted actions may be useful.
        # NOTE TO SELF III: Use dictionary to pass result?
        # Better yet, create class responses?
        if channel == "public":
            group_id = group_id
            # A group chat.
            if received_text[0] == "/":
                if received_text == self.keyword_join:
                    return self.include_participant(user_id, display_name)
                elif received_text == self.keyword_unjoin:
                    return self.exclude_participant(user_id)
                if received_text == self.keyword_continue_game:
                    return self.continue_game()
                elif received_text == self.keyword_history:
                    return self.show_history()
                elif received_text == self.keyword_scoreboard:
                    return self.show_scoreboard()
                elif received_text == self.keyword_show:
                    return self.show_banner()
                elif received_text == self.keyword_help:
                    return self.show_help()
                else:
                    return self.guess_word(user_id, received_text[1:])
            else:
                if len(received_text) == 1:
                    return self.guess(user_id, received_text)
                else:
                    # Common chat, ignore.
                    pass
        
        elif channel == "private":
            if received_text.split()[0] == keyword_add_word:
                return self.add_word(received_text.split(" ", 2)[1])
        

class Master:
    """
    Mastermind-type class to handle intermediary between LINE Messaging API
    and group-level Hangman module.
    
    BY DEFINITION, MASTERMIND IS TIED TO LINEBOTAPI.
    
    The Mastermind will accept an event from Messaging API, read where does it
    come from, and then pass it to respective Hangman instance. Afterwards,
    the Mastermind receives a Messenger class from Hangman instance, see what
    it requests, then deal with them.
    
    Mastermind only controls games and memberships. Every event is channeled to
    respective game instances and resolved there, except add_game and 
    remove_game. Both require Mastermind intervention to interact with games.
    """
    def __init__(self, line_bot_api):
        self.bot = line_bot_api
        self.games = {}
        self.memberships = {}
        self.keyword_add_game = "/gameon"        # "Give this group a (Hangman) game."
        self.keyword_remove_game = "/gameoff"    # "Remove game from this group."
        self.keyword_leave = "/goaway"           # "Leave from this group."
    
    def send_reply(self, token, messenger):
        reply_array = messenger.reply_array
        join_user = messenger.join_user
        unjoin_user = messenger.unjoin_user
        
        if join_user is not None:
            self.add_player_to_game(join_user)
        
        if unjoin_user is not None:
            pass
        
        chat_array = [TextSendMessage(text=u) for u in reply_array]
        self.bot.reply_message(
            token,
            chat_array
        )
    
    def add_player_to_game(self, user_id, group_id):
        if user_id not in self.memberships:
            self.memberships[user_id] = group_id
        pass
    
    def remove_player_from_game(self, user_id):
        if user_id in self.memberships:
            del self.memberships[user_id]
        pass
    
    def add_game(self, group_id, game):
        if group_id not in self.games:
            self.games[group_id] = game
        pass
    
    def remove_game(self, group_id):
        if group_id in self.games:
            self.memberships = {k: v for k, v in self.memberships.items() if v != group_id}
            del self.games[group_id]
        pass
    
    def leave_group(self, group_id):
        self.remove_game(group_id)
        self.bot.leave_group(group_id)
    
    def query_reply(self, token, channel, received_text, user_id, **kwargs):
        display_name = self.bot.get_profile(user_id).display_name
        if channel == "public":
            group_id = kwargs.get("group_id")
            # This is group chat, proceeds to listen to keywords:
            
            if received_text == self.keyword_leave:
                # A /goaway is received.
                if group_id in self.games:
                    self.send_reply(
                        token, channel,
                        self.games[group_id].show_goodbye()
                    )
                self.leave_group(group_id)
            
            elif group_id not in self.games:
                # No group in this game. Listen only to /gameon.
                if received_text.split()[0] == self.keyword_add_game:
                    try:
                        self.add_game(group_id, Hangman(int(received_text.split()[1]), int(received_text.split()[2])))
                    except (IndexError, ValueError) as error:
                        self.add_game(group_id, Hangman())
                    
                    self.send_reply(
                        token, channel,
                        self.games[group_id].show_hello()
                    )
                    
            else:
                # Group has active game, listen for /gameoff and keywords.
                if received_text == self.keyword_remove_game:
                    # A /gameoff is received.
                    self.send_reply(
                        token, channel,
                        self.games[group_id].show_goodbye()
                    )
                    self.remove_game(group_id)
                
                else:
                    # Master does not recognize, passes to Hangman.
                    self.send_reply(
                        token, channel,
                        self.games[group_id].parse_and_reply(
                            channel, received_text, user_id, display_name, group_id
                        )
                    )
        elif channel == "private":
            # Pass to Hangman, let it decide what to reply.
            if user_id in memberships:
                self.send_reply(
                    token, channel,
                    self.games[self.memberships[user_id]].parse_and_reply(
                        channel, received_text, user_id, display_name, group_id = None
                    )
                )

class TemplateGameClass:
    def __init__(self):
        pass
    
    def show_hello(self):
        reply_array = []
        return Messenger(reply_array)
    
    def show_goodbye(self):
        reply_array = []
        return Messenger(reply_array)
    
    def parse_and_reply(self, channel, received_text, user_id, display_name, group_id):
        reply_array = []
        return Messenger(reply_array)
