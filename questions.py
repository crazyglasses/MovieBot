class Question:
	Questions = []
	def __init__(self):
		self.Questions = []
		self.Questions.append("Hi . I am a movie bot. Can you please tell me your name ?") 
		self.Questions.append("Hi")
		self.Questions.append("Would you like to know the review about the movie?")
	def returnquestion(self,state=0):
		return self.Questions[state]