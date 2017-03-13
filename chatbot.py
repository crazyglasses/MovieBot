import nltk
from nltk.corpus import stopwords
import questions as Q
import subprocess
from nltk.corpus import names
import logging
logging.basicConfig()
import requests
import random
import sentiment as sent
from bs4 import BeautifulSoup
import unicodedata



from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import string
from nltk.stem import PorterStemmer
from nltk import word_tokenize

movies = {'action' : ['The Equalizer','Logan',' Mad Max: Fury Road','Rogue One','Star Wars'],'comedy' : ['Deadpool','The Nice Guys','Kingsman: The Secret Service','The Man from U.N.C.L.E.','Kung Fu Hustl '],'romance':['Titanic','The Notebook','When Harry Met Sally','Casablanca','Eternal Sunshine of the Spotless Min '],'horror':['Scary Movie','The Exorcist','The Shining','The Conjuring','Siniste '],'thriller':['Seven','Psycho','The Sixth Sense','Rear Window','Shutter Islan '],'adventure':['Hollywood Adventures','Raiders of the Lost Ark','The Lord of the Rings','Avatar','Jurassic Park']}

def train(classifier, xtrain, ytrain,xtest,ytest):

	classifier.fit(xtrain, ytrain)

	print "Accuracy: %s" % classifier.score(xtest, ytest)
	return classifier

def stemming_tokenizer(text):
	stemmer = PorterStemmer()
	return [stemmer.stem(w) for w in word_tokenize(text)]
 

trial1 = Pipeline([
    ('vectorizer', TfidfVectorizer(tokenizer=stemming_tokenizer,stop_words=stopwords.words('english'))),
    ('classifier', MultinomialNB()),
])



xtrain = ['Tell me about this movie',' I would like to know about this movie ','I think I want to know more about this movie ','Can you tell me more about this movie',' I want to know more about this movie','I want to know more about this movie','Can you suggest me a movie to watch?',' Suggest me a movie to watch ','Suggest me a movie to watch in ','I think I want to watch a movie ','I would like you to suggest me a movie']
ytrain = [0,0,0,0,0,0,1,1,1,1,1]


xtest = ['I want to know more this movie','What do you think about this movie?','I want more information about this movie','I would like you to suggest me a movie','Suggest me a movie','I would like suggestions']
ytest = [0,0,0,1,1,1]


class Bot:
	loop_flag = False
	QuestionObject = Q.Question()
	bot_state = None
	name = None
	detector0 = None
	movie  = None
	sentiment = None
	skip_state = False
	state_one_visited = False
	def __init__(self):
		self.loop_flag = True
		self.bot_state = 0
		self.QuestionObject = Q.Question()
		trial1 = Pipeline([
    			('vectorizer', TfidfVectorizer(tokenizer=stemming_tokenizer,stop_words=stopwords.words('english'))),
    			('classifier', MultinomialNB()),
			])
		self.detector0 = train(trial1, xtrain, ytrain,xtest,ytest )
		self.sentiment = sent.classifier()
	def conversationNotOver(self):
		return self.loop_flag
	def endConversation(self):
		self.loop_flag = False
	def question(self):
		if self.bot_state == 1:
			if not self.state_one_visited:
				self.state_one_visited = True
				return self.QuestionObject.returnquestion(self.bot_state) + " " + str(self.name) + ". Do you want to know about a movie or want me to suggest something you would like to watch ? "
			else:
				return " Do you want to know about a movie or want me to suggest something you would like to watch ? "
		return self.QuestionObject.returnquestion(self.bot_state)
	def extractnames(self,sentences):
		names = []
		for tagged_sentence in sentences:
			for chunk in nltk.ne_chunk(tagged_sentence):
				if type(chunk) == nltk.tree.Tree:
					if chunk.label() == 'PERSON':
						names.append(' '.join([c[0] for c in chunk]))
		return names


	def preprosess(self,response):
		stop = stopwords.words('english')
		response = ' '.join([i for i in response.split() if i not in stop])
		sentences = nltk.sent_tokenize(response)
		sentences = [nltk.word_tokenize(sent) for sent in sentences]
		sentences = [nltk.pos_tag(sent) for sent in sentences]
		if self.bot_state == 0:
			names = self.extractnames(sentences)
			if len(names) == 0:
				print "Movie Bot : Sorry , I couldn't get you ,  Could you please tell me your name?"
				self.name = raw_input('You : ')
			else:
				self.name = names[0]
		if self.bot_state == 1:
			label =  self.detector0.predict([str(response)])
			if label == 0:
				print "Movie Bot : Could you please tell the movie name?"
				moviename = raw_input('You : ')
				self.movie = moviename
				url = "http://www.omdbapi.com/?t=" + str(moviename)
				json = requests.get(url).json()
				try:
					print "Movie Bot : " + "The title of the movie is " + (json['Title']) + ". It was released in the year " + (json['Year']) + " and is a " + (json['Genre']) + " movie. It is directed by " + (json['Director']) + ". It has the following awards :" + (json['Awards'])
 				except:
 				 	print "Movie Bot : Sorry I couldn't understand"
 				 	self.skip_state = True

			elif label == 1:
				genre =  self.detectgenre(response)
				if genre in movies:
					self.movie =  movies[genre][random.randint(0,(len(movies[genre])-1))]
					print "Movie Bot : I suggest you to watch " + self.movie
				else:
					self.movie = movies['action'][random.randint(0,(len(movies[genre])-1))]
					print "Movie Bot : I suggest you to watch " + self.movie

		if self.bot_state == 2:

			if response.lower() == 'yes':
				url =  "https://api.nytimes.com/svc/movies/v2/reviews/search.json?api-key=73073227b3f343a384cb585053cd5a32&critics-pick=N&query=" + str(self.movie)
				json = requests.get(url).json()
				review_url =  str(json['results'][0]['link']['url']).replace('http://www.','https://')
				print "Movie Bot : You can read the complete review here . " + str(review_url)
				review = requests.get(review_url)
				soup = BeautifulSoup(review.text, 'html.parser')
				soup_review = soup.find_all("p", class_="story-body-text story-content")
				review_final = ''
				for x in soup_review:
					review_final = review_final + str(unicodedata.normalize('NFKD', x.get_text()).encode('ascii','ignore'))

				sent = self.sentiment.classify({'a' : review_final})
				if sent == 'pos':
					print "Movie Bot : After analysing the review, I think it is a good movie "
				if sent == 'neg':
					print "Movie Bot : After analysing the review, I think it is not a good movie "
				
					

				
				

	def detectgenre(self,sentence):
		
		url = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/ddba8f91-8175-4878-a28e-a91519272397?subscription-key=23183b4aa8e64c2bbb20bdc225dc257e&verbose=true&q=" + sentence
		try:
			json = requests.get(url).json()
		except: 
			print " I am not able to reach my server right now"

		genre = raw_input("Can you please tell me which genre movies do you like? ")
		return genre



	def next_state(self):
		if not self.skip_state:
			if self.bot_state == 2:
				self.bot_state = 0
			self.bot_state = self.bot_state + 1
		else:
			self.skip_state = False


subprocess.call("clear", shell=True)
bot = Bot()
while bot.conversationNotOver():
	print "Movie Bot : " + str(bot.question())
	response = raw_input("You  :  ")
	if 'bye' in response:
		bot.endConversation()

	bot.preprosess(response)
	bot.next_state()
	
	

