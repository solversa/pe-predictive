
def predictPE(inputDataLabel):
    confusions = dict()
  
    for holdout in batches:

        # Separate training and test data
        # Question - is there any reason to split via batches? Bias in this?
        train_set = [x for x in batches if x != holdout]
        test_impression = data[inputDataLabel][data.batch==holdout]
        test_labels = pandas.DataFrame(data['disease_state_label'][data.batch==holdout])
        test_ids = data['order_deid'][data.batch==holdout]
        train_impression = data[inputDataLabel][data.batch.isin(train_set)]
        train_labels = pandas.DataFrame(data['disease_state_label'][data.batch.isin(train_set)])
        train_ids = data['order_deid'][data.batch.isin(train_set)]

        train_labels["CLASS"] = "TRAIN"
        test_labels["CLASS"] = "TEST"
        allIds = train_ids.append(test_ids).tolist()
        allLabels = train_labels.append(test_labels)
        allLabels.index = allIds            

        # Make some strings for pretty printing of train/test batch
        training_ids = "|".join([str(int(x)) for x in train_set])
        testing_id = "%s" %(int(holdout))

        # Let's have a unique id so we can merge with whole report data later, eg 'holdout(2)-train(3|4)
        uid = "holdout(%s)-train(%s)" %(testing_id, training_ids)
   
        print("RUNNING ANALYSIS for %s:\n\ntrain(%s)\ntest(%s)" %(inputDataLabel,training_ids,testing_id,))
  
        # This object we can use to convert the impression/report into token counts
        countvec = CountVectorizer(ngram_range=(1,2),stop_words="english")
      
        # Train, and build ensemble classifier
        X_train = countvec.fit_transform(train_impression)
        clf = ensemble.ExtraTreesClassifier()
        clf.fit(X_train,train_labels['disease_state_label'])

        # Prepare test data in the same fashion, vectors of token counts, make predictions
        X_test = countvec.transform(test_impression)
        predictions = clf.predict(X_test.toarray())
        actual = test_labels['disease_state_label']

        # We want a score and a confusion matrix
        score = clf.score(X_test.toarray(),actual)
        print("Score: %s" %(score))
        labels = clf.classes_.tolist()
        confusion = makeConfusion(y_true=actual,
                                  y_pred=predictions,
                                  labels=labels)

        # Let's save the ones that we got wrong, index again by order ids
        gotwrong = pandas.DataFrame([[actual.index[x],test_impression.loc[actual.index[x]],predictions[x],actual.tolist()[x]] for x in range(len(predictions)) if predictions[x]!=actual.tolist()[x]])
        gotwrong.index = data.loc[gotwrong[0]].order_deid
        gotwrong = gotwrong.drop([0],axis=1)
        gotwrong.columns = [inputDataLabel,"PREDICTED","ACTUAL"]

        # Save confusion matrix, errors, and score for the batch
        result = {"confusion":confusion,
                  "score":score,
                  "errors":gotwrong}

        confusions[uid] = result

    return confusions

####################################################
# Analysis 1: Use impressions to classify PE 
####################################################

print("Preparing to do prediction with impression reports...")

impression_results = predictPE(inputDataLabel='impression')
pickle.dump(impression_results,open("data/impression_tree_results.pkl","wb"))

# RUNNING ANALYSIS for impression:

# train(3|4)
# test(2)
# Score: 0.911392405063

# train(2|4)
# test(3)
# Score: 0.842105263158

# train(2|3)
# test(4)
# Score: 0.725

####################################################
# Analysis 2: Use full rad reports to classify PE 
####################################################

print("Preparing to do prediction with full reports...")

report_results = predictPE(inputDataLabel='rad_report')
pickle.dump(report_results,open("data/report_tree_results.pkl","wb"))

# RUNNING ANALYSIS FOR rad_report:

# train(3|4)
# test(2)
# Score: 0.909282700422

# train(2|4)
# test(3)
# Score: 0.842105263158

# train(2|3)
# test(4)
# Score: 0.73123

