import pandas as pd
import sys
input_path  = sys.argv[1]
print("Relation Name \tTotal Instances\tpos. instances\tneg. instances\t same value\tpos. same value \tneg. same value\t False Negative \t False Positive \t same value False Negative \t same value False Positive")
df = pd.read_csv(input_path,sep='\t')
perc_eq =  df.loc[(df['mx'] == df['mt'])  &  (df['mTid'].str.contains('per'))]
perc_eq_1 = perc_eq.loc[perc_eq['GT'] == 'X1']
perc_eq_0 = perc_eq.loc[perc_eq['GT'] == 'X0']
perc_all = df.loc[(df['mTid'].str.contains('per'))]
perc_all_0 = perc_all.loc[perc_all['GT'] == 'X0']
perc_all_1 = perc_all.loc[perc_all['GT'] == 'X1']

perc_all_1_f = perc_all_1[perc_all_1['prob'] < 0.5]
perc_all_0_t = perc_all_0[perc_all_0['prob'] >0.5]

perc_eq_0_t = perc_eq_0.loc[perc_eq_0['prob'] > 0.5]
perc_eq_1_f = perc_eq_1.loc[perc_eq_1['prob'] <0.5]


print("percentage \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(perc_all.shape[0], perc_all_1.shape[0], perc_all_0.shape[0],perc_eq.shape[0], perc_eq_1.shape[0], perc_eq_0.shape[0], perc_all_1_f.shape[0], perc_all_0_t.shape[0], perc_eq_1_f.shape[0], perc_eq_0_t.shape[0]))


dif_eq = df.loc[(df['mx'] == df['mt'])  &  (df['mTid'].str.contains('dif'))]
dif_eq_1 = dif_eq.loc[dif_eq['GT'] == 'X1']
dif_eq_0 = dif_eq.loc[dif_eq['GT'] == 'X0']
dif_all = df.loc[(df['mTid'].str.contains('dif'))]
dif_all_0 = dif_all.loc[dif_all['GT'] == 'X0']
dif_all_1 = dif_all.loc[dif_all['GT'] == 'X1']


dif_all_1_f = dif_all_1[dif_all_1['prob'] < 0.5]
dif_all_0_t = dif_all_0[dif_all_0['prob'] >0.5]

dif_eq_0_t = dif_eq_0.loc[dif_eq_0['prob'] > 0.5]
dif_eq_1_f = dif_eq_1.loc[dif_eq_1['prob'] <0.5]

print("Difference \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(dif_all.shape[0], dif_all_1.shape[0], dif_all_0.shape[0],dif_eq.shape[0], dif_eq_1.shape[0], dif_eq_0.shape[0], dif_all_1_f.shape[0], dif_all_0_t.shape[0], dif_eq_1_f.shape[0], dif_eq_0_t.shape[0]))



rat_eq = df.loc[(df['mx'] == df['mt'])  &  (df['mTid'].str.contains('rat'))]
rat_eq_1 = rat_eq.loc[rat_eq['GT'] == 'X1']
rat_eq_0 = rat_eq.loc[rat_eq['GT'] == 'X0']
rat_all = df.loc[(df['mTid'].str.contains('rat'))]
rat_all_0 = rat_all.loc[rat_all['GT'] == 'X0']
rat_all_1 = rat_all.loc[rat_all['GT'] == 'X1']


rat_all_1_f = rat_all_1[rat_all_1['prob'] < 0.5]
rat_all_0_t = rat_all_0[rat_all_0['prob'] >0.5]

rat_eq_0_t = rat_eq_0.loc[rat_eq_0['prob'] > 0.5]
rat_eq_1_f = rat_eq_1.loc[rat_eq_1['prob'] <0.5]


print("Ratio \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(rat_all.shape[0], rat_all_1.shape[0], rat_all_0.shape[0],rat_eq.shape[0], rat_eq_1.shape[0], rat_eq_0.shape[0] , rat_all_1_f.shape[0], rat_all_0_t.shape[0], rat_eq_1_f.shape[0], rat_eq_0_t.shape[0]))



sum_eq = df.loc[(df['mx'] == df['mt'])  &  (df['mTid'].str.contains('sum'))]
sum_eq_1 = sum_eq.loc[sum_eq['GT'] == 'X1']
sum_eq_0 = sum_eq.loc[sum_eq['GT'] == 'X0']
sum_all = df.loc[(df['mTid'].str.contains('sum'))]
sum_all_0 = sum_all.loc[sum_all['GT'] == 'X0']
sum_all_1 = sum_all.loc[sum_all['GT'] == 'X1']

sum_all_1_f = sum_all_1[sum_all_1['prob'] < 0.5]
sum_all_0_t = sum_all_0[sum_all_0['prob'] >0.5]

sum_eq_0_t = sum_eq_0.loc[sum_eq_0['prob'] > 0.5]
sum_eq_1_f = sum_eq_1.loc[sum_eq_1['prob'] <0.5]


print("Sum \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(sum_all.shape[0], sum_all_1.shape[0], sum_all_0.shape[0],sum_eq.shape[0], sum_eq_1.shape[0], sum_eq_0.shape[0], sum_all_1_f.shape[0], sum_all_0_t.shape[0], sum_eq_1_f.shape[0], sum_eq_0_t.shape[0]))


avg_eq = df.loc[(df['mx'] == df['mt'])  &  (df['mTid'].str.contains('avg'))]
avg_eq_1 = avg_eq.loc[avg_eq['GT'] == 'X1']
avg_eq_0 = avg_eq.loc[avg_eq['GT'] == 'X0']
avg_all = df.loc[(df['mTid'].str.contains('avg'))]
avg_all_0 = avg_all.loc[avg_all['GT'] == 'X0']
avg_all_1 = avg_all.loc[avg_all['GT'] == 'X1']


avg_all_1_f = avg_all_1[avg_all_1['prob'] < 0.5]
avg_all_0_t = avg_all_0[avg_all_0['prob'] >0.5]

avg_eq_0_t = avg_eq_0.loc[avg_eq_0['prob'] > 0.5]
avg_eq_1_f = avg_eq_1.loc[avg_eq_1['prob'] <0.5]



print("Average \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(avg_all.shape[0], avg_all_1.shape[0], avg_all_0.shape[0],avg_eq.shape[0], avg_eq_1.shape[0], avg_eq_0.shape[0], avg_all_1_f.shape[0], avg_all_0_t.shape[0], avg_eq_1_f.shape[0], avg_eq_0_t.shape[0]))



same_eq = df.loc[(df['mx'] == df['mt'])  &  ~(df['mTid'].str.contains('avg') | df['mTid'].str.contains('per') | df['mTid'].str.contains('rat') | df['mTid'].str.contains('dif') | df['mTid'].str.contains('sum'))]

same_eq_1 = same_eq.loc[same_eq['GT'] == 'X1']
same_eq_0 = same_eq.loc[same_eq['GT'] == 'X0']
same_all = df.loc[~(df['mTid'].str.contains('avg') | df['mTid'].str.contains('per') | df['mTid'].str.contains('rat') | df['mTid'].str.contains('dif') | df['mTid'].str.contains('sum'))]
same_all_0 = same_all.loc[same_all['GT'] == 'X0']
same_all_1 = same_all.loc[same_all['GT'] == 'X1']


same_all_1_f = same_all_1[same_all_1['prob'] < 0.5]
same_all_0_t = same_all_0[same_all_0['prob'] >0.5]

same_eq_0_t = same_eq_0.loc[same_eq_0['prob'] > 0.5]
same_eq_1_f = same_eq_1.loc[same_eq_1['prob'] <0.5]


print("Single Cell \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(same_all.shape[0], same_all_1.shape[0], same_all_0.shape[0],same_eq.shape[0], same_eq_1.shape[0], same_eq_0.shape[0], same_all_1_f.shape[0], same_all_0_t.shape[0], same_eq_1_f.shape[0], same_eq_0_t.shape[0]))




