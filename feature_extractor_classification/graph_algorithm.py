import networkx as nx
import utils
import codecs
import glob
from sets import Set
import os
import sys
import numpy as np
tp = 0
tn =0 
fp =0
fn =0

accuracy ={}
for aggr in ['sum','same','dif','rat','percentage','avg']:
    accuracy[aggr] = {'tp':0,'tn':0,'fp':0, 'fn':0}

def accumelate_accuracy(cand, measure, count):
    global accuracy
    if 'sum' in cand:
        accuracy['sum'][measure] = accuracy['sum'][measure] + count 
    elif 'rat' in cand:
        accuracy['rat'][measure] = accuracy['rat'][measure] + count
    elif 'perc' in cand:
        accuracy['percentage'][measure] = accuracy['percentage'][measure] + count 

    elif 'avg' in cand:
        accuracy['avg'][measure] = accuracy['avg'][measure] + count 

    elif 'dif' in cand:
        accuracy['dif'][measure] = accuracy['dif'][measure] + count 

    else:
        accuracy['same'][measure] = accuracy['same'][measure] + count 


multi_correct_cand=0
alpha = 0.6 # stationary value
beta = 0.4 # prior
threshold = 0.5 # for selecting True relation
count_global_fn =0
count_global_fn2=0
lambda1 =0.9 # weight
lambda2 = 0.1 #surfaceform
#pairs.sort(key = lambda r : r[2],reverse=True) 

def start(path, priors_path):
    global accuracy, tn,tp,fn,fp,multi_correct_cand, count_global_fn2, count_global_fn
    tp =0
    tn =0
    fp=0
    fn =0
    multi_correct_cand =0
    count_global_fn2 =0
    count_global_fn =0
    accuracy ={}
    for aggr in ['sum','same','dif','rat','percentage','avg']:
        accuracy[aggr] = {'tp':0,'tn':0,'fp':0, 'fn':0}


    batches = [os.path.join(path,name) for name in os.listdir(path) if os.path.isdir(os.path.join(path,name)) and 'edges' in name ]
    all_priors = load_priors(priors_path)
    for batch in batches:
        solve_batch(batch,all_priors)
    #print("global fn %s"%count_global_fn2)
    print("Number of mentions with multiple matches: %s"%multi_correct_cand)
    print("tn\t:\t%s,\tfn:\t%s"%(tn,fn))
    print("fp\t:\t%s,\ttp:\t%s"%(fp,tp))
    pos = float(tp+fn)
    neg = float(tn+fp)
    sens = float(tp/pos) if pos !=0 else 0
    spec = float(tn/neg) if neg !=0 else 0
    accur = float(tn+tp)/float(pos+neg) if pos+neg != 0 else 0
    balanced_accuracy = float(sens +spec)/2.0
    print("Accuracy\t\tSensitivity\t\tSpecificity\t\tBalanced Accuracy")
    print("%s\t\t%s\t\t%s\t\t%s"%(accur,sens,spec,balanced_accuracy))

    for typ, val in accuracy.items():
        print("##############Type: %s  Results##############"%typ)
        tn_ = val['tn']
        fn_=val['fn']
        fp_= val['fp']
        tp_=val['tp']
        print("tn\t:\t%s,\tfn:\t%s"%(tn_,fn_))
        print("fp\t:\t%s,\ttp:\t%s"%(fp_,tp_))

        pos = float(tp_+fn_)
        neg = float(tn_+fp_)
        sens_ = float(tp_/pos) if pos !=0 else 0
        spec_ = float(tn_/neg) if neg !=0 else 0
        accur_ = float(tn_+tp_)/float(pos+neg) if pos+neg !=0 else 0
        balanced_accuracy_ = float(sens +spec)/2.0
        print("Accuracy\tSensitivity\tSpecificity\tBalanced Accuracy")
        print("%s\t\t%s\t\t%s\t\t%s"%(accur_,sens_,spec_,balanced_accuracy_))
    
    return sens,spec,accur, balanced_accuracy


    # Note that the FN rate increases as some X0 get prob value which is more than the correct class X1, thus it is picked as we pick the max!

def read_edges(file_name):
    return utils.read_tsv_as_dictionary(file_name, key =0)    

def get_distinct_mentions(priors):
    global count_global_fn
    mentions ={}
    for prior in priors:
        mention = prior[0]
        prob =float(prior[-1])
        if mention in mentions:
            mention_data = mentions[mention]
        else:
            mention_data =(mention,[])
        if prob >= threshold:
            mention_data[1].append(prob)
        elif prior[-6].strip() == 'X1':
            count_global_fn =count_global_fn + 1

        mentions[mention] = mention_data

        # sort mentions 
        mention_list = mentions.values()
        mention_list.sort(key = lambda r : (len(r[1]), -max(r[1]) if len(r[1]) > 0 else 0 ))

    return mention_list #Set(mentions)
def get_personalized_dict(nodes, mention):
    dic ={}
    for node in nodes:
        dic[node]=0
    dic[mention] =1 
    return dic

def solve_batch(path, all_priors):
        global  alpha, beta, threshold, tp,tn,fp,fn, accuracy
        files = glob.glob(path +'/part*')
        all_edges = utils.read_tsv_files(files, key =0)
        for doc, edges  in all_edges.items():
            if doc not in all_priors:
                continue

            priors = all_priors[doc]
            #print(priors)
            graph =  construct_graph(edges, priors)
            #print graph.edges()
            #return
            st_graph = nx.stochastic_graph(graph, copy=False)
            mentions = get_distinct_mentions(priors)
            m_graph = st_graph
            mapping_results =[]
            for mention, cand_priors in mentions:
                #remove edges connecting the mention to table cells
                # No need to copy as at the end we can re add the edge with the resolved mention only ;) /m_graph = st_graph.copy()
                candidates = get_candidates(mention, priors)

                if len(cand_priors) <=1:
                    for cand,cls,prob in candidates:
                        if cls =='X1':
                            if prob >= threshold:
                                tp= tp +1
                                accumelate_accuracy(cand, 'tp',1)
                                mapping_results.append("%s,%s,%s,%s,%s"%(doc,mention,cand,cls,prob))
                            else:
                                accumelate_accuracy(cand, 'fn',1)
                                fn = fn +1
                                
                        else:
                            if prob >=threshold:
                                mapping_results.append("%s,%s,%s,%s,%s"%(doc, mention,cand,cls,prob))
                                accumelate_accuracy(cand, 'fp',1)
                                fp = fp +1
                            else:
                                accumelate_accuracy(cand, 'tn',1)
                                tn = tn +1

                    
                    continue # already solved 
                    #TODO count in the accuracy / wrong/right match

                remove_mention_candidates_edges(m_graph, mention)
                #run random walk
                pers_dict = get_personalized_dict(m_graph.nodes(), mention)
                results = random_walk(m_graph, pers_dict)
                rescale_stationary_values(results, candidates)
                
                # get stationary distribution for candidates
                max_p =0.0
                winner = None
                winner_cls = None
                count_true_cand =0 
                for candidate,cls,prob in candidates:                    
                    #if candidate not in results:
                    #    continue
                    if cls.strip() =='X1':
                        count_true_cand = count_true_cand +1

                    p = results[candidate]
                    p = alpha * p + beta *prob
                    if p > max_p:
                        max_p = p
                        winner = candidate
                        winner_cls = cls
                if max_p >= threshold:
                    # resolve
                    # add edge to the graph with the max_p
                    m_graph.add_edge(mention, winner, weight= max_p)
                    mapping_results.append("%s,%s,%s,%s,%s"%(doc,mention,candidate,cls,prob))
                    
                #Compute accuracy for all candidates
                for cand,cls,prob in candidates:
                        if winner == cand and cls =='X1':
                            tp= tp +1
                            accumelate_accuracy(cand, 'tp',1)
                        elif winner == cand and cls =='X0':
                            accumelate_accuracy(cand, 'fp',1)
                            fp = fp +1
                        elif cls == 'X0':
                            tn = tn+1
                            accumelate_accuracy(cand, 'tn',1)
                        else:
                            fn = fn +1 
                            accumelate_accuracy(cand,'fn',1)

                #####################
                '''if winner_cls =='X1':
                    #correct
                        accumelate_accuracy(candidate, 'tp',1)
                        accumelate_accuracy(cand, 'tn',len(candidates)-1)
                        tp = tp +1
                        tn = tn + len(candidates)-1

                    else:
                        accumelate_accuracy(candidate, 'fp',1)
                        accumelate_accuracy(candidate, 'tn',len(candidates)-1)
                        fp = fp +1
                        tn= tn + len(candidates)-1
                        if count_true_cand > 0:
                            accumelate_accuracy(candidate, 'fn',1)
                            accumelate_accuracy(candidate, 'tn',-1)
                            fn = fn + 1
                            tn = tn -1

                        
                elif count_true_cand > 0:
                    # missed annotation
                    accumelate_accuracy(candidate, 'fn',count_true_cand)
                    accumelate_accuracy(candidate, 'tn',len(candidates) - count_true_cand)
                    fn = fn + count_true_cand
                    tn = tn + len(candidates)-count_true_cand
                else:
                    accumelate_accuracy(candidate, 'tn',len(candidates))
                    tn = tn + len(candidates)
                    # check if mention has any true candidates  
                '''
                # count correct #precision 
        #print(mapping_results)


def get_candidates(mention, priors):
    global multi_correct_cand, count_global_fn2, threshold
    correct_cand =0
    candidates =[]
    for prior in priors:
        if prior[0] != mention:
            continue
        #only consider candidates of the given mention 
        candidate = prior[1]
        prob =float( prior[-1])
        cls = prior[-6].strip()
        if prob >= threshold:
            correct_cand = correct_cand +1
        candidates.append((candidate,cls,prob))
    if correct_cand >1:
        multi_correct_cand = multi_correct_cand +1

    return candidates

def remove_mention_candidates_edges(graph, mention):
    neighbors = graph.neighbors(mention)
    for neighbor in neighbors:
        if '.' in  neighbor:#table mention ID
            graph.remove_edge(mention, neighbor)

            
def load_priors(file_name):
    return utils.read_tsv_as_dictionary(file_name, key =1)


def construct_graph(edges, priors):
    global lambda1, lambda2
    graph = nx.DiGraph()
    for edge in edges:
        node1 = edge[0]
        node2 = edge[1]
        weight = float(edge[2])
        surfaceform_sim = float(edge[3])
        value_diff = float(edge[4])
        weight = lambda1 * weight + lambda2 * surfaceform_sim #value_diff
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(node1,node2, weight = weight)
        graph.add_edge(node2,node1, weight = weight)
        #print("Edge between %s, %s with weight %s"%(node1,node2,weight))
        #graph.add_weighted_edges_from([(node1,node2,weight), (node2,node1,weight)]) #bi-directional
    for prior in priors:
        node1 = prior[0]
        node2 = prior[1]
        weight = float(prior[-1])

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(node1,node2,weight = weight) # from mention to table and not vice versa 
        #print("Edge from %s to %s with weight %s"%(node1,node2,weight))
    return graph

def random_walk(graph, personalization_dict):
    return nx.pagerank_scipy(graph,personalization = personalization_dict)
def rescale_stationary_values(results, candidates):
    total = 0.0
    for cand,_,_ in candidates:
        total += results[cand]
    for cand,_,_ in candidates:
        results[cand] = results[cand]/total
def generate_params_values():
    values = []

    for alpha in np.linspace(0, 1, 11):
        beta = 1- alpha
        for threshold in np.linspace(0,0.5,6):
            for lambda1 in np.linspace(0,1,11):
                lambda2 = 1- lambda1
                values.append((alpha,beta,threshold, lambda1, lambda2))
    return values


def param_tuning():
    global alpha, beta, threshold, lambda1, lambda2
    # tune alpha, beta, threshold, lambda1, lambda2
    print ("alpha\tbeta\tthreshold\tlambda1\tlambda2")
    #values =[(0.1,0.9,0.5,0.9, 0.1),(0.2,0.8, 0.5,0.9,0.1),(0.3,0.7,0.5,0.9,0.1),(0.4,0.6,0.5,0.9,0.1),(0.5,0.5,0.5,0.9,0.1),(0.6,0.4,0.5,0.9,0.1),(0.7,0.3,0.5,0.9,0.1)]
    values = generate_params_values()

    best_params = None 
    best_accuracy =0
    for alpha_, beta_, threshold_, lambda1_, lambda2_ in values:
        alpha = alpha_
        beta = beta_
        threshold= threshold_
        lambda1 = lambda1_
        lambda2 = lambda2_
        print ("#######################################################################")
        print ("alpha\tbeta\tthreshold\tlambda1\tlambda2")
        print("%s\t\t%s\t\t%s\t\t%s\t\t%s"%(alpha,beta, threshold, lambda1, lambda2))

        try:
            sens,spec,accur, balanced_accur = start('/GW/D5data-8/yibrahim/script/FeaturesExtractor/results_final_2neg/','/GW/D5data-8/yibrahim/script/FeaturesExtractor/output_plus_prob_RF_m2_dev.tsv' )

            if balanced_accur > best_accuracy:
                best_accuracy = balanced_accur
                best_params = (alpha,beta,threshold,lambda1,lambda2)
        except:
            print("Could not tune for params %s\t\t%s\t\t%s\t\t%s\t\t%s"%(alpha,beta, threshold, lambda1, lambda2))

        sys.stdout.flush()
    print("Best accuracy: %s"%best_accuracy)
    print("Best params: Alpha\tbeta\tthreshold\t,lambda1, lambda2")
    print("%s\t%s\t%s\t%s\t%s"%best_params)

param_tuning()
#print(generate_params_values())

#print(accuracy)
#start('test', 'test/priors.tsv')
def test():
        #priors = load_priors('/GW/D5data-8/yibrahim/script/FeaturesExtractor/output_plus_prob.tsv')
        #solve_batch('/GW/D5data-8/yibrahim/script/FeaturesExtractor/second_run/edges1',priors)
        #print (priors)

        edges =[['1','2','0.5','0.3', '0.2'],['2','3','0.2','0.3','0.2'],['4.2','5.4','0.6','0.5','0.9'],['7.3','6.1','0.1','0.05','.9']]
        priors =[['1','6.1','hg',0,1,1,0,'0.7'],['2','7.3', 'jsjs',1,0,1,1,'0.7'],['2','5.4','hdh','iei',1,1,1,1,'0.6'],['3','7.3','gsh',1,1,1,0,'0.2']]
        print(get_distinct_mentions(priors))
        g = construct_graph(edges, priors)
        print("graph edges %s"%g.edges())
    
        print("2 neighbors %s"%g.neighbors('2'))
        print("mentions %s"%get_distinct_mentions(priors))
        print("2 candidates %s"%get_candidates('2', priors))
        remove_mention_candidates_edges(g, '2')
        print("Updated 2 neigbors %s"%g.neighbors('2'))

        results= {'1':0.009,'2':0.01, '3':0.00001, '4':0.01}
        candidates =[('1','ksk',0.7),('2','kks', 0.5),('3','jks',0.1)]
        rescale_stationary_values(results, candidates)
        print(results)
        #start('/GW/D5data-8/yibrahim/script/FeaturesExtractor/second_run/')
#test()
