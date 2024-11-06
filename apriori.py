import sys
import os.path
import csv
import math 
import types
from collections import defaultdict
from collections.abc import Iterable
import itertools

# Kelas Apriori untuk menemukan itemset yang sering dan menghasilkan aturan asosiasi
class Apriori:
    def __init__(self, data, minSup, minConf):
        # Inisialisasi variabel utama
        self.dataset = data
        self.transList = defaultdict(list)  # Menyimpan daftar transaksi
        self.freqList = defaultdict(int)  # Menyimpan frekuensi item
        self.itemset = set()  # Menyimpan item yang unik
        self.highSupportList = list()  # Menyimpan item dengan support tinggi
        self.numItems = 0  # Total jumlah item
        self.prepData()  # Menyiapkan data transaksi

        self.F = defaultdict(list)  # Menyimpan itemset yang sering

        self.minSup = minSup  # Nilai minimum support
        self.minConf = minConf  # Nilai minimum confidence

    # Menghasilkan asosiasi untuk itemset yang sering
    def genAssociations(self):
        candidate = {}
        count = {}

        # Pemindaian pertama untuk menemukan item satu-item yang sering
        self.F[1] = self.firstPass(self.freqList, 1)
        k = 2
        while len(self.F[k-1]) != 0:  # Iterasi hingga tidak ada lagi itemset yang sering
            candidate[k] = self.candidateGen(self.F[k-1], k)  # Menghasilkan kandidat itemset
            # Menghitung frekuensi setiap kandidat pada data transaksi
            for t in self.transList.items():
                for c in candidate[k]:
                    if set(c).issubset(t[1]):
                        self.freqList[c] += 1

            self.F[k] = self.prune(candidate[k], k)  # Menghapus itemset yang tidak memenuhi syarat
            if k > 2:
                self.removeSkyline(k, k-1)  # Menghilangkan subset yang tidak perlu
            k += 1

        return self.F

    # Menghapus subset yang tidak perlu dari itemset yang sering
    def removeSkyline(self, k, kPrev):
        for item in self.F[k]:
            subsets = self.genSubsets(item)
            for subset in subsets:
                if subset in self.F[kPrev]:
                    self.F[kPrev].remove(subset)

    # Memfilter itemset berdasarkan nilai support
    def prune(self, items, k):
        f = []
        for item in items:
            count = self.freqList[item]
            support = self.support(count)
            # Jika support >= 0.95, tambahkan ke daftar highSupportList
            if support >= .95:
                self.highSupportList.append(item)
            # Jika memenuhi minimum support, tambahkan ke itemset yang sering
            elif support >= self.minSup:
                f.append(item)

        return f

    # Menghasilkan kandidat itemset dengan menggabungkan itemset sebelumnya
    def candidateGen(self, items, k):
        candidate = []

        if k == 2:
            # Menggabungkan dua item jika panjangnya dua
            candidate = [tuple(sorted([x, y])) for x in items for y in items if len((x, y)) == k and x != y]
        else:
            # Menggabungkan itemset yang lebih besar
            candidate = [tuple(set(x).union(y)) for x in items for y in items if len(set(x).union(y)) == k and x != y]
        
        # Memfilter kandidat yang tidak memenuhi syarat
        for c in candidate:
            subsets = self.genSubsets(c)
            if any([x not in items for x in subsets]):
                candidate.remove(c)

        return set(candidate)

    # Menghasilkan semua subset dari suatu itemset
    def genSubsets(self, item):
        subsets = []
        for i in range(1, len(item)):
            subsets.extend(itertools.combinations(item, i))
        return subsets

    # Menghasilkan aturan asosiasi dari itemset yang sering
    def genRules(self, F):
        H = []

        for k, itemset in F.items():
            if k >= 2:
                for item in itemset:
                    subsets = self.genSubsets(item)
                    for subset in subsets:
                        # Mendapatkan count subset dan item
                        if len(subset) == 1:
                            subCount = self.freqList[subset[0]]
                        else:
                            subCount = self.freqList[subset]
                        itemCount = self.freqList[item]
                        # Menghitung confidence dan menambahkan aturan jika memenuhi syarat
                        if subCount != 0:
                            confidence = self.confidence(subCount, itemCount)
                            if confidence >= self.minConf:
                                support = self.support(self.freqList[item])
                                rhs = self.difference(item, subset)
                                if len(rhs) == 1:
                                    H.append((subset, rhs, support, confidence))

        return H

    # Menghitung perbedaan antara item dan subset
    def difference(self, item, subset):
        return tuple(x for x in item if x not in subset)

    # Menghitung nilai confidence dari suatu aturan
    def confidence(self, subCount, itemCount):
        return float(itemCount) / subCount

    # Menghitung nilai support dari suatu itemset
    def support(self, count):
        return float(count) / self.numItems

    # Pemindaian pertama untuk item satu-item yang sering
    def firstPass(self, items, k):
        f = []
        for item, count in items.items():
            support = self.support(count)
            if support == 1:
                self.highSupportList.append(item)
            elif support >= self.minSup:
                f.append(item)

        return f

    # Menyiapkan data transaksi menjadi format kamus
    def prepData(self):
        key = 0
        for basket in self.dataset:
            self.numItems += 1
            key = basket[0]
            for i, item in enumerate(basket):
                if i != 0:
                    self.transList[key].append(item.strip())
                    self.itemset.add(item.strip())
                    self.freqList[(item.strip())] += 1

# Fungsi utama untuk mengelola input dan memulai algoritma
def main():
    goods = defaultdict(list)
    num_args = len(sys.argv)
    minSup = minConf = 0
    noRules = False

    # Memeriksa jumlah argumen input yang benar
    if num_args < 4 or num_args > 5:
        print('Expected input format: python apriori.py <dataset.csv> <minSup> <minConf>')
        return
    elif num_args == 5 and sys.argv[1] == "--no-rules":
        dataset = csv.reader(open(sys.argv[2], "r"))
        goodsData = csv.reader(open('goods.csv', "r"))
        minSup = float(sys.argv[3])
        minConf = float(sys.argv[4])
        noRules = True
        print("Dataset: ", sys.argv[2], " MinSup: ", minSup, " MinConf: ", minConf)
    else: 
        dataset = csv.reader(open(sys.argv[1], "r"))
        goodsData = csv.reader(open('goods.csv', "r"))
        minSup = float(sys.argv[2])
        minConf = float(sys.argv[3])
        print("Dataset: ", sys.argv[1], " MinSup: ", minSup, " MinConf: ", minConf)

    print("==================================================================")

    # Membaca deskripsi item dari goods.csv
    for item in goodsData:
        goods[item[0]] = item[1:]

    # Membuat objek Apriori dan menemukan itemset yang sering
    a = Apriori(dataset, minSup, minConf)
    frequentItemsets = a.genAssociations()

    # Menampilkan itemset yang sering
    count = 0
    for k, item in frequentItemsets.items():
        for i in item:
            if k >= 2:
                count += 1
                print(count, ":  ", readable(i, goods), "\tsupport=", a.support(a.freqList[i]))

    print("Skyline Itemsets: ", count)
    # Jika aturan diminta, menghasilkan dan menampilkan aturan asosiasi
    if not noRules:
        rules = a.genRules(frequentItemsets)
        for i, rule in enumerate(rules):
            print("Rule", i + 1, ":\t ", readable(rule[0], goods), "\t-->", readable(rule[1], goods), "\t [sup=", rule[2], " conf=", rule[3], "]")

    print("\n")

# Fungsi untuk menghasilkan format yang lebih mudah dibaca untuk itemset
def readable(item, goods):
    itemStr = ''
    for k, i in enumerate(item):
        itemStr += goods[i][0] + " " + goods[i][1] + " (" + i + ")"
        if len(item) != 0 and k != len(item) - 1:
            itemStr += ",\t"

    return itemStr.replace("'", "")

# Memulai program jika dijalankan sebagai skrip utama
if __name__ == '__main__':
    main()
