
##################################################

##################################################

# Veri setiFlo’danson alışverişlerini 2020 -2021 yıllarında OmniChannel(hem online hem offline alışveriş yapan)
# olarak yapan müşterilerin geçmiş alışveriş davranışlarından elde edilen bilgilerden oluşmaktadır.


# master_id : Eşsiz Müşteri numarası
# order_channel : Alışveriş yapılan platforma ait hangi kanalın kullanıldığı (Android, ios, Desktop, Mobile)
# last_order_channel : En son alışveriş yapılan kanal
# firs_order_date : Müşterinin yaptığı ilk alışveriş tarihi
# last_order_date : Müşterinin yaptığı son alışveriş tarihi
# last_order_date_online : Müşterinin online platformda yaptığı son alışveriş tarihi
# last_order_date_offline: Müşterinin offline platformda yaptığı son alışveriş tarihi
# order_num_total_ever_offline : Müşterinin offline'da yaptığı toplam alışveriş sayısı
# order_num_total_ever_online : Müşterinin online platformda yaptığı toplam alışveriş sayısı
# customer_value_total_ever_offline : Müşterinin offline alışverişlerinde ödediği toplam ücret
# customer_value_total_ever_online : Müşterinin online alışverişlerinde ödediği toplam ücret
# interested_in_categories_12 : Müşterinin son 12 ayda alışveriş yaptığı kategorilerin listesi Veri Seti Hikayesi


##################################
# 1. Veri hazırlama
##################################

import pandas as pd
import datetime as dt
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.float_format", lambda  x: "%.2f" % x)
pd.set_option("display.width", 1000)

df_ = pd.read_csv("CRM/CRM_datasets/flo_data_20k.csv")

df = df_.copy()
df.head()

# Veri setinde
# a. İlk 10 gözlem,
# b. Değişken isimleri,
# c. Boyut
# d. betimsel istatistik
# e.boş değer
# f. Değişken tipleri, incelemesi

df.head(10)

df.columns
df.shape
df.describe().T
df.isnull().sum()
df.info()

# Omnichannel müşterilerin hem online'dan hemde offline platformlardan alışveriş yaptığını ifade etmektedir.
#  Her bir müşterinin toplam alışveriş sayısı ve harcaması için yeni değişkenler oluşturalım

df["order_num_total"] = df["order_num_total_ever_online"] + df["order_num_total_ever_offline"]

df["customer_value_total"] = df["customer_value_total_ever_offline"] + df["customer_value_total_ever_online"]


# Değişken tipleri inceleme.Tarih değişkenini date e çevirme

df.info()
date_columns = df.columns[df.columns.str.contains("date")]
df[date_columns] = df[date_columns].apply(pd.to_datetime)
df.info()

#  Alışveriş kanallarındaki müşteri sayısının, toplam alınan ürün sayısının ve toplam harcamaların dağılımına bakalım.

df.groupby("order_channel").agg({"master_id": "count",
                                 "order_num_total": "sum",
                                 "customer_value_total": "sum"})

#  En fazla kazancı getiren ilk 10 müşteri sıralama
df.sort_values("customer_value_total", ascending=False)[:10]

# En fazla alış veriş yapan 10 müşteri
df.sort_values("order_num_total", ascending=False)[:10]

# veri ön hazırlık sürecinin fonksiyonlaştırma

def data_prep(dataframe):
    dataframe["order_num_total"] = dataframe["order_num_total_ever_online"] + \
                                   dataframe["order_num_total_ever_offline"]

    dataframe["customer_value_total"] = dataframe["customer_value_total_ever_offline"] + \
                                        dataframe["customer_value_total_ever_online"]

    date_cloumns = dataframe.columns[dataframe.columns.str.contains("date")]
    dataframe[date_cloumns] = dataframe[date_cloumns].apply(pd.to_datetime)
    return df


##################################
# RFM Metriklerinin hesaplanması
##################################

# veri setindeki en son alışverişin yapıldığı tarihten 2 gün sonrasını analiz tarihi olarak alalım
df["last_order_date"].max()  # 2021-05-30
analysis_date = dt.datetime(2021,6,1)

# customer_id, recency, frequnecy ve monetary değerlerinin olduğu bir rfm dataframe

rfm = pd.DataFrame()
rfm["customer_id"] = df["master_id"]
rfm["recency"] = (analysis_date - df["last_order_date"]).astype("timedelta64[D]")
rfm["frequency"] = df["order_num_total"]
rfm["monetary"] = df["customer_value_total"]

rfm.head()

# Recency, Frequency ve Monetary metriklerini qcut yardımı ile 1 ile 5
# arasında skorlara çevrilmesi

rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1])
rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])  # rank ile ilk gördüğün veriyi al diyoruz
rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5])

rfm.head()

# recency_score ve frequency_score' u tek bir değişken olarak ifade edilmesi ve
# RFM_SCORE olarak kaydedilmesi
# amaç bunları segmentlere ayırmak
rfm["RFM_SCORE"] = (rfm["recency_score"].astype(str) + rfm["frequency_score"].astype(str))

# recency_score, frequency_score ve monetary_score'u tek bir değişken olarak
# ifade edilmesi ve RFM_SCORE olarak kaydedilmesi
rfm["RFM_SCOREE"] = (rfm["recency_score"].astype(str) + rfm["monetary_score"].astype(str) + rfm["frequency_score"].astype(str))

rfm.head()


##################################
# RF Skorlarının Segment Olarak Tanımlanması
##################################

# Oluşturulan RFM skorların daha açıklanabilir olması için segment tanımlama ve
# tanımlanan seg_map yardımı ile RF_SCOREE'u segmentlere çevirme

seg_map = {
    r'[1-2][1-2]': "hibernating",
    r'[1-2][3-4]': "at_Risk",
    r'[1-2]5': "cant_Loose",
    r'3[1-2]': "about_to_sleep",
    r'33': "need_attention",
    r'[3-4][4-5]': "loyal_customers",
    r'41': "promising",
    r'51': "new_customers",
    r'[4-5][2-3]': "potential_loyalists",
    r'5[4-5]': "champions"
}

rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)

rfm.head()


# Segmentlerin recency, frequency ve monetary ortalamalarını inceleyelim

rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])


# FLO bünyesine yeni bir kadın ayakkabı markası dahil ediyor.Dahil ettiği markanın ürün fiyatları genel müşteri tercihlerinin üstünde.
# Bu nedenle markanın tanıtımı ve ürün satışları için ilgilenecek profildeki müşterilerle özel olarak iletişime geçmek isteniliyor.
# Sadık müşterilerinden(champions,loyal_customers) ve kadın kategorisinden alışveriş yapan kişiler özel olarak iletişim kurulacak müşteriler.
# Bu müşterilerin id numaralarını csvdosyasına kaydediniz.

target_segments_customer_ids = rfm[rfm["segment"].isin(["champions", "loyal_customers"])]["customer_id"]

cust_ids = df[(df["master_id"].isin(target_segments_customer_ids)) &
              (df["interested_in_categories_12"].str.contains("KADIN"))]["master_id"]

cust_ids.to_csv("Yeni_Marka_müşteri_id.csv", index= False)

cust_ids.shape
cust_ids.head()
rfm.head()



# Erkek ve Çocuk ürünlerinde %40'a yakın indirim planlanmaktadır.Bu indirimle ilgili kategorilerle ilgilenen
# geçmişte iyi müşteri olan ama uzun süredir alışveriş yapmayan kaybedilmemesi gereken müşteriler,
# uykuda olanlar ve yeni gelen müşteriler özel olarak hedef alınmak isteniyor.
# Uygun profildeki müşterilerin id'lerini csv dosyasına kaydediniz.

target_segments_customer_ids = rfm[rfm["segment"].isin(["cant_Loose", "hibernating", "new_customers"])]["customer_id"]

cust_ids = df[(df["master_id"].isin(target_segments_customer_ids) &
               (df["interested_in_categories_12"].str.contains("ERKEK")) |
               (df["interested_in_categories_12"].str.contains("COCUK")))]["master_id"]

cust_ids.to_csv("indirim_hedef_müşteri_ids.csv", index= False)

cust_ids.shape
cust_ids.head()


