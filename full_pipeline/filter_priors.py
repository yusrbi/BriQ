import utils
import sys 
from random import shuffle
from scipy import stats


missed = 0
total_pos =0
missed_by_id={}
total_pos_by_id = {}
ids= '4,5,7,8,9,10,11,12,13,14,15,16,26'.split(',')

for id_ in ids:
    pos = int(id_)
    missed_by_id[pos]=0
    total_pos_by_id[pos]=0

recall ={}
total={}

for aggr in ['sum','same','dif','rat','perc','avg', 'exact']:
    recall[aggr] = {'True':0, 'False':0}
    total[aggr] = {'True':0, 'False':0}
cls_indx = -2

def main():
    global missed, total_pos, recall, missed_by_id, total_pos_by_id, total
    if len(sys.argv) < 4:
        print("Please specify the prior file, the output file, and k")
    file_name = sys.argv[1]
    output_name = sys.argv[2]
    k = int(sys.argv[3])
    priors = utils.load_priors_by_mention_id(file_name)
    #TODO get base_line classification here!    
    print_base_line_results(priors)

    mention_class = utils.load_mention_classifications("mention_classification_test_all")

    filtered_priors =[]
    baseline_filtered ={}
    for mention_id in priors.keys():
        if mention_id == 'mXId':
            # first line, just append to the front of the list
            priors[mention_id][0].append("aggr_prob")
            filtered_priors.insert(0, priors[mention_id][0])
            continue

        filtered_ = adaptive_filtering(priors[mention_id],mention_class[mention_id][0],  k) #filter_mention_3(priors[mention_id], k) #
        #TODO
        #print_conflicts(filtered_)
        filtered_priors.extend(filtered_)
        baseline_filtered[mention_id] = filtered_

    print("Base Line + Filtering :")
    print_base_line_results(baseline_filtered)


    for key in missed_by_id.keys():
        print("%s,%s"%(key,missed_by_id[key]))
    print(total_pos_by_id)

    print("relation\tincluded\tmissed\ttotal\trecall")
    total_inc =0
    total_missed =0
    total_total =0

    for relation in recall.keys():
        total_ = recall[relation]['True']+recall[relation]['False'] 
        if total_ == 0:
            total_ =1
        print("%s\t%d\t%d\t%d\t%s"%(relation, recall[relation]['True'], recall[relation]['False'],total_, float(recall[relation]['True'])/total_))
        if relation is not 'exact':
            total_inc = total_inc + recall[relation]['True']
            total_missed = total_missed + recall[relation]['False']
            total_total = total_total + total_
    print("%s\t%d\t%d\t%d\t%s"%("all", total_inc, total_missed,total_total, float(total_inc)/total_total))


    print("Stats on all for selectivity:")
    total_inc =0
    total_missed =0
    total_total =0

    for relation in total.keys():
        total_ = total[relation]['True']+total[relation]['False'] 

        if total_ == 0:
            total_ =1
        print("%s\t%d\t%d\t%d\t%s"%(relation, total[relation]['True'], total[relation]['False'],total_, float(total[relation]['True'])/total_))
        if relation is not 'exact':
            total_inc = total_inc + total[relation]['True']
            total_missed = total_missed + total[relation]['False']
            total_total = total_total + total_
    print("%s\t%d\t%d\t%d\t%s"%("all", total_inc, total_missed,total_total, float(total_inc)/total_total))

    print(" missed items %s"%missed)
    print("Total pos. inst %s"%total_pos)
    utils.write_list_as_tsv(output_name, filtered_priors)

def print_base_line_results(all_priors):
    global cls_indx
    count={}
    for aggr in ['all','sum','avg','rat','dif','percentage','same']:
        count[aggr] ={}
        for k in ['tp','tn','fp','fn']:
            count[aggr][k] =0

    for mention, priors in all_priors.items():
        if mention == 'mXId':
            continue
        if not priors:
            continue

        priors.sort(key = lambda prior: float(prior[-1]), reverse= True )  
        for i in range(len(priors)):
            answer = priors[i]
            cls = answer[cls_indx]
            aggr_fnc = utils.get_aggr_fnc_from_id(answer[3])
            #print(cls)
            if i==0 and float(answer[-1]) >= 0.5:
                related = True
            else:
                related = False

            if related and cls == 'X1':
                count['all']['tp'] +=1
                count[aggr_fnc]['tp']+=1
            elif not related and cls !='X1':
                count['all']['tn']+=1
                count[aggr_fnc]['tn']+=1
            elif related and cls != 'X1':
                count['all']['fp'] += 1
                count[aggr_fnc]['fp']+=1
            else:
                count['all']['fn']+=1
                count[aggr_fnc]['fn']+=1

    print ("### Baseline Results###")

    for relation, counts in count.items():
        print(relation)
        try:
            accuracy = float(counts['tp']+counts['tn'])/float(counts['tp']+counts['fp']+counts['tn']+counts['fn'])
        except:
            accuracy =0 

        try:
            p = float(counts['tp'])/float(counts['tp']+counts['fp'])
        except:
            p =0
        try:
            r = float(counts['tp'])/float(counts['tp']+counts['fn'])
        except:
            r =0 
        if r != 0 and p !=0:
            f1 = 2.0/((1.0/r)+(1.0/p))
        else:
            f1 =0 

        print("TN\t:\t%s, \tFN:\t%s"%(str(counts['tn']),str(counts['fn'])))
        print("FP\t:\t%s, \tTP:\t%s"%(str(counts['fp']),str(counts['tp'])))
        print("accuracy,recall, precision, F1")
        print("%s"%str(accuracy))
        print("%s"%str(r))
        print("%s"%str(p))
        print("%s"%str(f1))


    return count 


def count_all(cand, is_included, is_exact):
    global total
    count = 1
    if 'sum' in cand:
        total['sum'][str(is_included)] = total['sum'][str(is_included)] + count
    elif 'rat' in cand:
        total['rat'][str(is_included)] = total['rat'][str(is_included)] + count
    elif 'perc' in cand:
        total['perc'][str(is_included)] = total['perc'][str(is_included)] + count

    elif 'avg' in cand:
        total['avg'][str(is_included)] = total['avg'][str(is_included)] + count

    elif 'dif' in cand:
        total['dif'][str(is_included)] = total['dif'][str(is_included)] + count

    else:
        total['same'][str(is_included)] = total['same'][str(is_included)] + count
    #check on exact match or not 
    if is_exact:
        total['exact'][str(is_included)] = total['exact'][str(is_included)] + count

def count_pos(cand, is_included, is_exact):
    global recall
    count = 1
    
    if 'sum' in cand:
        recall['sum'][str(is_included)] = recall['sum'][str(is_included)] + count
    elif 'rat' in cand:
        recall['rat'][str(is_included)] = recall['rat'][str(is_included)] + count
    elif 'perc' in cand:
        recall['perc'][str(is_included)] = recall['perc'][str(is_included)] + count

    elif 'avg' in cand:
        recall['avg'][str(is_included)] = recall['avg'][str(is_included)] + count

    elif 'dif' in cand:
        recall['dif'][str(is_included)] = recall['dif'][str(is_included)] + count

    else:
        recall['same'][str(is_included)] = recall['same'][str(is_included)] + count
        #check on exact match or not 
        if is_exact:
            recall['exact'][str(is_included)] = recall['exact'][str(is_included)] + count
def print_conflicts(mention_pairs):
    global cls_indx
    cls = cls_indx

    prior = -1
    gt_prior = 0.0
    has_gt = False
    for mention_pair in mention_pairs:
        if mention_pair[cls] =='X1':
            gt_prior = mention_pair[prior]
            print("has GT:")
            print('\t'.join(mention_pair))
            has_gt = True
    if has_gt:
        for mention_pair in mention_pairs:
            if mention_pair[prior] > gt_prior:
                print('\t'.join(mention_pair))
    #else:


def filter_mention(priors, k):
    global missed , total_pos, cls_indx
    #shuffle(priors)

    priors.sort(key = lambda prior: float(prior[-2]), reverse= True ) #max(float(prior[4]), float(prior[5])), reverse = True) 
    answer = None
    count = 0
    top_k =[]
    for prior in priors:
        cls = prior[cls_indx-1]
        mx = prior[-10-1]
        mt= prior[-9-1]
        unit_match =prior[9]
        aggr_fn_match =prior[10]
        prob = prior[-1-1]
        is_exact = False
        if mx == mt:
            is_exact = True
        if cls == 'X1':
            total_pos = total_pos +1
        if count < k:
            #if unit_match == '-1':# or  aggr_fn_match =='-1':
            #    if cls == 'X1':
            #        print("missed in uint/aggr mismatch")
            #        count_pos(prior[3], False, is_exact)
            #    #count_all(prior[3], True, is_exact)
            #    count_all(prior[3],False, is_exact)

            #    continue # skip in case non matching unit and non matching aggregate function
            
            if cls == 'X1':
                count_pos(prior[3], True, is_exact)
                #count_all(prior[3], True, is_exact)
            count_all(prior[3],True, is_exact)
            top_k.append(prior)
            count = count +1
        else:
            if cls == 'X1':
            #print("missed answer")
            #if is_exact:
            #    print('\t'.join(prior))
                missed = missed + 1
                count_pos(prior[3], False, is_exact)
            count_all(prior[3], False, is_exact)
        

    #top_k = priors[:min(k, len(priors))]

    return top_k
def prune(mention_pairs, mention_class):
    if not mention_class:
        print(mention_pairs[1], mention_pairs[2])
        return 
    #print(mention_class)
    global cls_indx 
    pruned_mention_pairs = []
    sim_no_scale = 4
    sim_max = 5 
    dif_sum = 6
    prior = -1
    gt = cls_indx
    surface_form_sim = 15
    pred_mention_class = mention_class[-6]
    map_cls_prob ={"percentage":-5,"rat":-4,"sum":-3,"dif":-2,"same":-1}
    aggregates=["percentage","rat","sum","dif","same"]
    prob = mention_class[-5:]
    prob = enumerate(prob)
    prob = sorted(prob,key= lambda x:x[1],reverse=True)
    #print("probabilities sorted",prob)
    second_pred_mention_class = aggregates[prob[1][0]]

    #print("second predicyions", second_pred_mention_class)
  
    for pair in mention_pairs:
        value_sim = max(float(pair[sim_no_scale]), float(pair[sim_max]) )
        mx = pair[-10]
        mt= pair[-9]
        prob = pair[-1]
        is_exact = False
        if mx == mt:
            is_exact = True
        aggr_fnc = utils.get_aggr_fnc_from_id(pair[3])
        if aggr_fnc in map_cls_prob:
            aggr_prob = float(mention_class[map_cls_prob[aggr_fnc]])
        else:
            aggr_prob = 0.0#should not be any case 
        include = False
        #print(aggr_fnc, pred_mention_class, second_pred_mention_class)
        if aggr_fnc =='same':
            include = True # include all same

        #1- include mention pair if it matches the pred_mention_class, in case it is not same 
        elif pred_mention_class != 'same':

            if aggr_fnc == pred_mention_class:
                #print("match")
                include = True
            #else:
            #    print(aggr_fnc, pred_mention_class)
            # elif aggr_fn == 'dif' and pred_mention_class =='sum':
            #     include = True
            # elif aggr_fn == 'sum' and pred_mention_class == 'dif':
            #     include = True
            # elif aggr_fn == 'percentage' and pred_mention_class == 'rat':
            #   include = True
        else: #same
            #get 2nd aggregate function
            
            if aggr_fnc == second_pred_mention_class:
                #print("match 2")
                include = True
            elif aggr_fnc == 'dif' and second_pred_mention_class =='sum':
                #print("diff to sum")
                include = True
            elif aggr_fnc == 'sum' and second_pred_mention_class == 'dif':
                #print("sum to dif")
                include = True
            elif aggr_fnc == 'percentage' and second_pred_mention_class == 'rat':
                #print("percentage to ratio")
                include = True

        ####TODO use classification here 
        if value_sim < 0.9 or  not include:#not included
            if pair[gt] == 'X1':
                print("missed of prune")
                count_pos(pair[3], False, is_exact)
            count_all(pair[3], False, is_exact)
            continue

        #else:#included -- no need to count them now 
        #    if pair[gt] == 'X1':
        #        count_pos(pair[3], True, is_exact)
        #    count_all(pair[3], True, is_exact)

 #                print pair
        #pair[-1] = str(float(pair[-1])*0.2 +aggr_prob * 0.8)
        pair.append(str(aggr_prob))
        pruned_mention_pairs.append(pair)
    #if len(pruned_mention_pairs) != len(mention_pairs):
    #    print("count after  pruning is %d"%len(pruned_mention_pairs))
    #    print("count before pruning is %d"%len(mention_pairs))

    return pruned_mention_pairs
def get_pair_type(mx, mt):
    if mx == mt:
        return 'exact'
    elif len(mx) >  len(mt) and mx[:len(mt)] == mt:
        return 'truncated'
    elif len(mt) >  len(mx) and mt[:len(mx)] == mx:
        return 'truncated'
    else:
        return 'approximate'

def get_mention_type(mention_pairs):
    exact_count =0
    approx_count =0
    trunc_count =0
    mention_pairs.sort(key = lambda pair :float( pair[-1]), reverse = True)
    limit = 5 # only consider the top 5 mention pairs to estimate the mention type
    count = 0
    for pair in mention_pairs:
        count = count +1
        if count > limit:
            break
        pair_type = get_pair_type(pair[17], pair[18])

        if pair_type =='exact':
            exact_count = exact_count +1
        elif pair_type == 'approximate':
            approx_count = approx_count + 1
        else: #truncated
            trunc_count = trunc_count + 1
    mention_type =''
    if exact_count > approx_count and exact_count > trunc_count:
        mention_type = 'exact'
    elif approx_count > exact_count and approx_count > trunc_count:
        mention_type ='approximate'
    else:
        mention_type = 'truncated'
    return mention_type

def adaptive_filtering(mention_pairs, mention_class, k):
    global missed_by_id, total_pos_by_id, ids
    shuffle(mention_pairs)
        #step one get rid of the very unlikely mention pairs
    mention_pairs = prune(mention_pairs, mention_class) # no need to do it now as in the feature extraction this is taken care of
    priors = [float(mention_pair[-2]) for mention_pair in mention_pairs]
    mention_type = get_mention_type(mention_pairs)

    entropy = stats.entropy(priors)
    if mention_type == 'exact':
        k = 5
    elif entropy < 3.0:
        k = 10
    #elif entropy < 5.0:
    #    k = 7
    else:
        k = 15
    #print(entropy, k)
   

    return filter_mention(mention_pairs, k)


def filter_mention_3(priors,k):
    global missed_by_id, total_pos_by_id, ids, cls_indx
    shuffle(priors)

    for id_ in ids:
        pos = int(id_)
        priors_sorted = sorted(priors, key = lambda prior:float(prior[pos]), reverse= True ) 
        count =0 
        for prior in priors_sorted:
            count = count +1
            cls = prior[cls_indx]
            if cls == 'X1':
                total_pos_by_id[pos]  = total_pos_by_id[pos] +1
            if count > k and cls == 'X1':
                missed_by_id[pos] = missed_by_id[pos] +1 
    return []
        
def filter_mention_2(priors, k):
    global missed , total_pos, cls_indx
    shuffle(priors)

    priors.sort(key = lambda prior:float(prior[16]), reverse= True ) #float(prior[-1]), reverse = True)
    answer = None
    count = 0
    top_k =[]
    for prior in priors:
        cls = prior[cls_indx]
        mx = prior[-10]
        mt= prior[-9]
        prob = float(prior[-1])
        approx_sim = float(prior[-11])
        sf_sim = float( prior[-12])
        ltokn_sim = float(prior[10])
        lnp = float(prior[11])

        is_exact = False
        if mx == mt:
            is_exact = True
        if cls == 'X1':
            total_pos = total_pos +1
        if count < k:
            if cls == 'X1':
                count_pos(prior[3], True, is_exact)
            top_k.append(prior)
            count = count +1
        #elif prob > 0.9:
        #    if cls == 'X1':
        #        count_pos(prior[3], True, is_exact)
        #    top_k.append(prior)
        #    count = count + 1
        elif cls == 'X1':
            #print("missed answer")
            #if is_exact:
            #    print('\t'.join(prior))
            missed = missed + 1
            count_pos(prior[3], False, is_exact)
            break
    #top_k = priors[:min(k, len(priors))]

    return top_k


def test():
    print('1.24','1.2',get_pair_type('1.24','1.2'))
    print('1.26','1.3',get_pair_type('1.26','1.3'))
    print('782.9','782.9',get_pair_type('782.9','782.9'))
    print('50001','5000',get_pair_type('50001','5000'))
    print('240','243',get_pair_type('234','230'))
    print('240','243',get_pair_type('240','243'))
    print('1500','1550',get_pair_type('1500','1550'))

if __name__ == '__main__':
    main()
    #test()
