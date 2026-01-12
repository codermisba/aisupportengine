from recommender import KnowledgeRecommender

recommender = KnowledgeRecommender()

ticket = "I forgot my password and cannot log into my account"

results = recommender.recommend(ticket)

for r in results:
    print(r)
