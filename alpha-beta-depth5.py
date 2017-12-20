# -*- coding: utf-8 -*

# ソケット通信クライアント

import socket
import re
import time
import copy
import sys
from operator import itemgetter

#対局を進める
class Taikyoku:
    def __init__(self, teban_num):
        self.from_masu = "S1"
        self.to_masu = "S1"
        self.teban_n = teban_num

    def yomitori(self, s, BUFSIZE):
        s.send(("board\n").encode())
        time.sleep(0.1)

        self.board_in_str = s.recv(BUFSIZE).rstrip().decode()  #文字列で返されている

        self.board = {}  #局面の状態
        self.koma = {}  #両者の駒
        self.koma_p1 = {}
        self.koma_p2 = {}
        self.mochigoma_d = {"D1": "--", "D2": "--", "D3": "--",
                            "D4": "--", "D5": "--", "D6": "--"}
        self.mochigoma_e =  {"E1": "--", "E2": "--", "E3": "--",
                             "E4": "--", "E5": "--", "E6": "--"}
        self.aki = {}  #空きマス

        for mk in self.board_in_str.split(","):  # mk-> m:masu, k:koma
            mk = mk.strip()

            if mk != "" and mk != "moved.":
                self.board[mk.split(" ")[0]] = mk.split(" ")[1]
                if mk.split(" ")[1] != "--":
                    self.koma[mk.split(" ")[0]] = mk.split(" ")[1]

                elif mk.split(" ")[1] == "--":
                    if  mk.split(" ")[0][0] != "E" and  mk.split(" ")[0][0] != "D":
                        self.aki[mk.split(" ")[0]] = mk.split(" ")[1]

                if mk.split(" ")[1][1] == "1":
                    self.koma_p1[mk.split(" ")[0]] = mk.split(" ")[1]

                if mk.split(" ")[1][1] == "2":
                    self.koma_p2[mk.split(" ")[0]] = mk.split(" ")[1]

                if mk.split(" ")[0][0] == "D":
                    self.mochigoma_d[mk.split(" ")[0]] = mk.split(" ")[1]

                if mk.split(" ")[0][0] == "E":
                    self.mochigoma_e[mk.split(" ")[0]] = mk.split(" ")[1]


    def saki_yomitori_b(self, boardInfo):
        self.board = copy.deepcopy(boardInfo) #ボードの状態


    def saki_yomitori_a(self, boardInfo):
        self.aki = {} #空きマス

        for masu, koma in boardInfo.items():
            if koma == "--":
                if masu[0] != "D" and masu[0] != "E":
                    self.aki[masu] = koma


    def saki_yomitori_p(self, boardInfo):
        self.koma_p1 = {}
        self.koma_p2 = {}
        for masu, koma in boardInfo.items():
            if koma != "--":
                if koma[1] == "1":
                    self.koma_p1[masu] = koma
                elif koma[1] == "2":
                    self.koma_p2[masu] = koma


    def saki_yomitori_m(self, boardInfo):
        self.mochigoma_d = {"D1": "--", "D2": "--", "D3": "--",
                            "D4": "--", "D5": "--", "D6": "--"}
        self.mochigoma_e =  {"E1": "--", "E2": "--", "E3": "--",
                             "E4": "--", "E5": "--", "E6": "--"}
        for masu, koma in boardInfo.items():
            if masu[0] == "D":
                self.mochigoma_d[masu] = koma
            elif masu[0] == "E":
                self.mochigoma_e[masu] = koma


    def display_kyoku(self):
        banmen, koma_d, koma_e = henkan_masu_to_list(self.board)
        for index in range(len(koma_e)):
            sys.stdout.write(koma_e[index] + " ")
        print("\n")

        for y in range(4):
            sys.stdout.write("    ")
            for x in range(3):
                sys.stdout.write(banmen[y][x] + " ")
            print("\n")

        for index in range(len(koma_d)):
            sys.stdout.write(koma_d[index] + " ")
        print("\n")


    def kenchi(self, kyoku_bf, kyoku_af):
        able = []
        opp_teban_n = get_opp_teban_n(self.teban_n)
        km_move, fr_ms, to_ms = serch_opp_te(kyoku_bf, kyoku_af, self.teban_n)
        my_km, opp_km = conv_my_opp(kyoku_bf, self.teban_n)
        kyoku = Taikyoku(teban_n)
        kyoku.saki_yomitori_a(kyoku_bf)
        taple_kiki = serch_kiki(fr_ms, km_move, my_km, kyoku.aki, opp_teban_n)
        for i in range(len(taple_kiki)):
            able.append(taple_kiki[i][2])
        if fr_ms[0] != "D" and fr_ms[0] != "E":
            if to_ms in able:
                pass
            else:
                print("foul")
                time.sleep(2.0)


    def chakushu(self, s):
        if self.teban_n == "1":
            from_masu, to_masu = tansaku(self.board, self.teban_n)
        elif self.teban_n == "2":
            from_masu, to_masu = tansaku(self.board, self.teban_n)

        s.send(("mv " + from_masu + " " + to_masu + "\n").encode())
        time.sleep(0.1)


    def hantei(self):
        winner_c = hantei_catch(self.board, self.teban_n)
        winner_t = hantei_try(self.board, self.teban_n)
        if winner_c:
            return winner_c
        elif winner_t:
            return winner_t


def serch_opp_te(kyoku_bf, kyoku_af, teban_n):
    #持ち駒は排除する
    bf = {}
    af = {}
    km = "S1"
    opp_te = []
    to_ms = "S1"
    fr_ms = "S1"
    for ms_b, km_b in kyoku_bf.items():
        if ms_b[0] != "D" and ms_b[0] != "E":
            bf[ms_b] = km_b
    for ms_a, km_a in kyoku_af.items():
        if ms_a[0] != "D" and ms_a[0] != "E":
            af[ms_a] = km_a

    for ms_b, km_b in bf.items():
        for ms_a, km_a in af.items():
            if ms_b == ms_a:
                if km_b != km_a:
                    opp_te.append((ms_a, km_a))
    opp_teban_n = get_opp_teban_n(teban_n)
    for i in range(len(opp_te)):
        if opp_te[i][1][1] == opp_teban_n:
            to_ms = opp_te[i][0]
            km = opp_te[i][1]
        else:
            fr_ms = opp_te[i][0]
    if fr_ms == "S1":
        if teban_n == "1":
            fr_ms = "E7"
        else:
            fr_ms = "D7"
    return km, fr_ms, to_ms


#@引数　文字列　from_masu
#      文字列　koma
#      辞書　opponent_dict　　　　　　対戦相手の駒が置かれているマスと駒の辞書
#      辞書　aki_dict　　　　　　　　　駒の置かれていないマスの辞書
#      文字列　teban_n　　　　　　　　　手番のプレイヤー番号　文字１か２で表す
#
#@返り値　リスト　list_taple　　　着手可能マスのタプル（koma, bf,af）を格納したリスト
def serch_kiki(from_masu, koma, opponent_dict, aki_dict, teban_n):
    list_from_to = []
    board_from_to = []
    list_taple = []
    if from_masu[0] == "D" or from_masu[0] == "E":
        board_from_to = [masu for masu in aki_dict.keys()]
    elif from_masu[0] == "A" or from_masu[0] == "B" or from_masu[0] == "C":
        from_masu_in_list = masu_in_board_to_list(from_masu)
        bf_tate_list = int(from_masu_in_list[0])
        bf_yoko_list = int(from_masu_in_list[1])
        if koma[0] == "l":
            serch_lion(list_from_to, bf_tate_list, bf_yoko_list)
        elif koma[0] == "g":
            serch_giraffe(list_from_to, bf_tate_list, bf_yoko_list)
        elif koma[0] == "e":
            serch_elephant(list_from_to, bf_tate_list, bf_yoko_list)
        elif koma[0] == "c":
            serch_chick(list_from_to, bf_tate_list, bf_yoko_list, teban_n)
        elif koma[0] == "h":
            serch_chicken(list_from_to, bf_tate_list, bf_yoko_list, teban_n)
        for i in range(len(list_from_to)):
            masu_in_list = list_from_to[i]
            masu_in_board = masu_in_list_to_board(masu_in_list)
            if masu_in_board in opponent_dict or masu_in_board in aki_dict:
                board_from_to.append(masu_in_board)
    for i in range(len(board_from_to)):
        taple_from_to = (koma, from_masu, board_from_to[i])
        list_taple.append(taple_from_to)
    return list_taple


def serch_giraffe(list_from_to, bf_tate_list, bf_yoko_list):
    af_tate_list = bf_tate_list + 1
    if af_tate_list <= 3:
        af_list = str(af_tate_list) + str(bf_yoko_list)
        list_from_to.append(af_list)

    af_tate_list = bf_tate_list - 1
    if af_tate_list >= 0:
        af_list = str(af_tate_list) + str(bf_yoko_list)
        list_from_to.append(af_list)

    af_yoko_list = bf_yoko_list + 1
    if af_yoko_list <= 2:
        af_list = str(bf_tate_list) + str(af_yoko_list)
        list_from_to.append(af_list)

    af_yoko_list = bf_yoko_list - 1
    if af_yoko_list >= 0:
        af_list = str(bf_tate_list) + str(af_yoko_list)
        list_from_to.append(af_list)


def serch_elephant(list_from_to, bf_tate_list, bf_yoko_list):
    af_tate_list = bf_tate_list + 1
    if af_tate_list <= 3:
        af_yoko_list = bf_yoko_list + 1
        if af_yoko_list <= 2:
            af_list = str(af_tate_list) + str(af_yoko_list)
            list_from_to.append(af_list)

        af_yoko_list = bf_yoko_list - 1
        if af_yoko_list >= 0:
            af_list = str(af_tate_list) + str(af_yoko_list)
            list_from_to.append(af_list)

    af_tate_list = bf_tate_list - 1
    if af_tate_list >= 0:
        af_yoko_list = bf_yoko_list + 1
        if af_yoko_list <= 2:
            af_list = str(af_tate_list) + str(af_yoko_list)
            list_from_to.append(af_list)

        af_yoko_list = bf_yoko_list - 1
        if af_yoko_list >= 0:
            af_list = str(af_tate_list) + str(af_yoko_list)
            list_from_to.append(af_list)


def serch_lion(list_from_to, bf_tate_list, bf_yoko_list):
    serch_giraffe(list_from_to, bf_tate_list, bf_yoko_list)
    serch_elephant(list_from_to, bf_tate_list, bf_yoko_list)


def serch_chick(list_from_to, bf_tate_list, bf_yoko_list, teban_n):
    if teban_n == "1":
        af_tate_list = bf_tate_list - 1
        if af_tate_list >= 0:
            af_list = str(af_tate_list) + str(bf_yoko_list)
            list_from_to.append(af_list)
    elif teban_n == "2":
        af_tate_list = bf_tate_list + 1
        if af_tate_list <= 3:
            af_list = str(af_tate_list) + str(bf_yoko_list)
            list_from_to.append(af_list)

def serch_chicken(list_from_to, bf_tate_list, bf_yoko_list, teban_n):
    if teban_n == "1":
        serch_giraffe(list_from_to, bf_tate_list, bf_yoko_list)

        af_tate_list = bf_tate_list - 1
        if af_tate_list >= 0:
            af_yoko_list = bf_yoko_list + 1
            if af_yoko_list <= 2:
                af_list = str(af_tate_list) + str(af_yoko_list)
                list_from_to.append(af_list)

            af_yoko_list = bf_yoko_list - 1
            if af_yoko_list >= 0:
                af_list = str(af_tate_list) + str(af_yoko_list)
                list_from_to.append(af_list)

    elif teban_n == "2":
        serch_giraffe(list_from_to, bf_tate_list, bf_yoko_list)

        af_tate_list = bf_tate_list + 1
        if af_tate_list <= 3:
            af_yoko_list = bf_yoko_list + 1
            if af_yoko_list <= 2:
                af_list = str(af_tate_list) + str(af_yoko_list)
                list_from_to.append(af_list)

            af_yoko_list = bf_yoko_list - 1
            if af_yoko_list >= 0:
                af_list = str(af_tate_list) + str(af_yoko_list)
                list_from_to.append(af_list)


def hantei_catch(board, teban_n):
    catch_kyoku = Taikyoku(teban_n)
    catch_kyoku.saki_yomitori_m(board)

    winner = None
    for koma in catch_kyoku.mochigoma_d.values():
        if koma == "l1":
            winner = "p1"
    for koma in catch_kyoku.mochigoma_e.values():
        if koma == "l2":
            winner = "p2"
    return winner


#can_go_masuの中身の例
#[('l2', 'B2', 'C3'), ('l2', 'B2', 'A3'), ... ,('g2', 'A2', 'A1')]
#
def hantei_try(board, teban_n):
    winner = None
    opp_teban_n = get_opp_teban_n(teban_n)
    can_go_masu_my = make_can_go_masu(board, teban_n)
    can_go_masu_opp = make_can_go_masu(board, opp_teban_n)

    if teban_n == "1":
        can_go_masu_p1 = can_go_masu_my
        can_go_masu_p2 = can_go_masu_opp
    elif teban_n == "2":
        can_go_masu_p2 = can_go_masu_my
        can_go_masu_p1 = can_go_masu_opp
    dest_p1 = []
    dest_p2 = []
    dest_p1 = [i[2] for i in can_go_masu_p1]
    dest_p2 = [i[2] for i in can_go_masu_p2]

    for masu, koma in board.items():
        if koma == "l1" and masu[1] == "1":
            if masu in dest_p2:
                pass
            else:
                winner = "p1"
        if koma == "l2" and masu[1] == "4":
            if masu in dest_p1:
                pass
            else:
                winner = "p2"
    return winner


def ab_max(board, teban_n, depth, alpha, beta):
#    if depth == 4:
#        print("depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))
#    if depth == 3:
#        print("  depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))
#    if depth == 2:
#        print("    depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))
#    if depth == 1:
#        print("      depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))

    best_bf_masu = "S1"
    best_af_masu = "S1"

    can_go_masu = make_can_go_masu(board, teban_n)

    shallow = []
    for i in range(len(can_go_masu)):
        board_child = {}
        #手を指して次の局面を作る
        koma = can_go_masu[i][0]
        bf_masu = can_go_masu[i][1]
        af_masu = can_go_masu[i][2]

        #駒を動かす
        board_child = move_koma(koma, bf_masu, af_masu, board, teban_n)

        #判定
        kyoku_h = Taikyoku(teban_n)
        kyoku_h.saki_yomitori_b(board_child)
        judge = kyoku_h.hantei()
        if judge:
            if judge[1] == teban_n:
#                print("win cutting")
                return 600, bf_masu, af_masu

        #子ノードへ移る前の浅い探索評価
        shallow.append((koma, bf_masu, af_masu, evaluate(board_child, teban_n)))
    #評価の高い順にソートする
    shallow.sort(key=itemgetter(3), reverse=True)

    if depth == 2:
        bf_masu = shallow[0][1]
        af_masu = shallow[0][2]
        val = shallow[0][3]
#        print("      depth: 1" + " alpha: " + str(alpha) + " beta: " + str(beta))
        return val, bf_masu, af_masu

    for i in range(len(shallow)):
        board_child = {}
        #手を指して次の局面を作る
        koma = shallow[i][0]
        bf_masu = shallow[i][1]
        af_masu = shallow[i][2]

        #駒を動かす
        board_child = move_koma(koma, bf_masu, af_masu, board, teban_n)

        #子ノードへ移る
        val, bf, af = ab_min(board_child, teban_n, depth - 1, alpha, beta)

        if val > alpha:
            alpha = val
            best_bf_masu = bf_masu
            best_af_masu = af_masu
            if alpha >= beta:
#               print("cut")
                return beta, best_bf_masu, best_af_masu
    return alpha, best_bf_masu, best_af_masu


def ab_min(board, teban_n, depth, alpha, beta):
#    if depth == 4:
#        print("depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))
#    if depth == 3:
#        print("  depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))
#    if depth == 2:
#        print("    depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))
#    if depth == 1:
#        print("      depth: " + str(depth) + " alpha: " + str(alpha) + " beta: " + str(beta))

    best_bf_masu = "S1"
    best_af_masu = "S1"

    opp_teban_n = get_opp_teban_n(teban_n)
    can_go_masu = make_can_go_masu(board, opp_teban_n)

    shallow = []
    for i in range(len(can_go_masu)):
        board_child = {}
        #手を指して次の局面を作る
        koma = can_go_masu[i][0]
        bf_masu = can_go_masu[i][1]
        af_masu = can_go_masu[i][2]

        #駒を動かす
        board_child = move_koma(koma, bf_masu, af_masu, board, opp_teban_n)

        #判定
        kyoku_h = Taikyoku(opp_teban_n)
        kyoku_h.saki_yomitori_b(board_child)
        judge = kyoku_h.hantei()
        if judge:
            if judge[1] == opp_teban_n:
#                print("win cutting")
                return -600, bf_masu, af_masu

        #子ノードへ移る前の浅い探索評価
        shallow.append((koma, bf_masu, af_masu, evaluate(board_child, opp_teban_n)))
    #評価の低い順にソートする
    shallow.sort(key=itemgetter(3))

    if depth == 2:
        bf_masu = shallow[0][1]
        af_masu = shallow[0][2]
        val = shallow[0][3]
#        print("      depth: 1" + " alpha: " + str(alpha) + " beta: " + str(beta))
        return val, bf_masu, af_masu

    for i in range(len(shallow)):
        board_child = {}
        #手を指して次の局面を作る
        koma = shallow[i][0]
        bf_masu = shallow[i][1]
        af_masu = shallow[i][2]

        #駒を動かす
        board_child = move_koma(koma, bf_masu, af_masu, board, opp_teban_n)

        #子ノードへ移る
        val, bf, af = ab_max(board_child, teban_n, depth - 1, alpha, beta)

        if val < beta:
            beta = val
            best_bf_masu = bf_masu
            best_af_masu = af_masu
            if beta <= alpha:
#                print("cut")
                return alpha, best_bf_masu, best_af_masu
    return beta, best_bf_masu, best_af_masu


def alpha_beta(board, teban_n, depth, alpha, beta):
    best_val, best_bf_masu, best_af_masu = ab_max(board, teban_n, depth, alpha, beta)
#    print("best_val, best_bf_masu, best_af_masu")
#    print(str(best_val) + " " + best_bf_masu + " " + best_af_masu)
    return best_bf_masu, best_af_masu


#@引数　辞書　board
#　　　　文字列　teban_n
#
#@返り値　文字列　from_masu　　　　　最善手で動かす前のマス
#        文字列　to_masu　　　　　　最善手で動かす先のマス
def tansaku(board, teban_n):
    from_masu = "S1"
    to_masu = "S1"

    INF_P = 10000
    INF_N = -10000
    depth = 6
    alpha = INF_N
    beta = INF_P
    from_masu, to_masu = alpha_beta(board, teban_n, depth, alpha, beta)

    return from_masu, to_masu


def make_can_go_masu(board, teban_n):
    go_kyoku = Taikyoku(teban_n)
    go_kyoku.saki_yomitori_a(board)
    my_koma, opp_koma = conv_my_opp(board, teban_n)
    can_go_masu = []
    for masu, my_km in my_koma.items():
        board_from_to = serch_kiki(masu, my_km, opp_koma,
                                   go_kyoku.aki, teban_n)
        can_go_masu.extend(board_from_to)
    return can_go_masu


#@引数　文字列　koma　　　　　　　　　　動かす駒
#      文字列　bf_koma　　　　　　　　　移動前のマス
#      文字列　af_koma　　　　　　　　　移動後のマス
#      辞書　board
#      文字列　teban_n　　　　　　　　　手番のプレイヤー番号　文字１か２で表す
#
#@返り値　辞書　board
def move_koma(koma, bf_koma, af_koma, board, teban_n):
    move_kyoku = Taikyoku(teban_n)
    move_kyoku.saki_yomitori_b(board)
    move_kyoku.saki_yomitori_a(board)
    my_koma, opp_koma = conv_my_opp(board, teban_n)

    if af_koma in move_kyoku.aki:
        #put koma
        move_kyoku.board[bf_koma] = "--"
        koma = convert_chick_to_chicken(koma, bf_koma, af_koma)
        move_kyoku.board[af_koma] = koma

    elif af_koma in opp_koma:
        #read foe_koma
        target_koma = opp_koma[af_koma]
        #rewrite foe to mine
        koma_gotten = target_koma[0] + teban_n
        #put foe_koma in koma_kiba
        koma_okiba = find_koma_okiba(board, teban_n)
        koma_gotten = convert_chicken_to_chick(koma_gotten)
        move_kyoku.board[koma_okiba] = koma_gotten

        #put koma
        move_kyoku.board[bf_koma] = "--"
        koma = convert_chick_to_chicken(koma, bf_koma, af_koma)
        move_kyoku.board[af_koma] = koma

    return move_kyoku.board


def convert_chick_to_chicken(koma, bf_koma, af_koma):
    if koma[0] == "c":
        if bf_koma[1] == "3" and af_koma[1] == "4":
            koma = "h" + koma[1]
        elif bf_koma[1] == "2" and af_koma[1] == "1":
            koma = "h" + koma[1]
    return koma


def convert_chicken_to_chick(koma_gotten):
    if koma_gotten[0] == "h":
        koma_gotten = "c" + koma_gotten[1]
    return koma_gotten


#@引数　辞書　board
#　　　　文字列　teban_n
#
#@返り値　文字列　koma_okiba　　　　　　　取った持ち駒を置く場所
def find_koma_okiba(board, teban_n):
    okiba_kyoku = Taikyoku(teban_n)
    okiba_kyoku.saki_yomitori_m(board)

    koma_okiba = "S1"
    i_min = 10
    if teban_n == "1":
        for masu, koma in okiba_kyoku.mochigoma_d.items():
            if koma == "--":
                if i_min > int(masu[1]):
                    i_min = int(masu[1])
        koma_okiba = "D" + str(i_min)
    if teban_n == "2":
        for masu, koma in okiba_kyoku.mochigoma_e.items():
            if koma == "--":
                if i_min > int(masu[1]):
                    i_min = int(masu[1])
        koma_okiba = "E" + str(i_min)

    return koma_okiba


#@引数　辞書　board
#　　　　文字列　teban_n
#
#@返り値　整数値　value　　　　　　　　評価の値
def evaluate(board, teban_n):
    score_piece = eval_piece(board, teban_n)
    score_diff_kiki = eval_difference_kiki(board, teban_n)
    score_hantei = eval_hantei(board, teban_n)
    score_kata = eval_kata(board, teban_n)
    score = [score_piece, score_diff_kiki, score_hantei, score_kata]
    value = sum(score)

    return value


#@引数　辞書　board
#　　　　文字列　teban_n
#
#@返り値　整数値　score　　　　　評価の値
def eval_piece(board, teban_n):
    my_koma, opp_koma = conv_my_opp(board, teban_n)

    score = 0
    for masu, koma in my_koma.items():
        if masu[0] == "D" or masu[0] == "E":  #持ち駒
            if koma[0] == "g":
                score += 3
            elif koma[0] == "e":
                score += 3
            elif koma[0] == "c":
                score += 1
        else:  #盤上の駒
            if koma[0] == "g":
                score += 5
            elif koma[0] == "e":
                score += 5
            elif koma[0] == "c":
                score += 4
            elif koma[0] == "h":
                score += 8
            elif koma[0] == "l":
                score += 50
    return score


#@引数　辞書　board
#　　　　文字列　teban_n
#
#@返り値　整数値　score　　　　　　評価の値
def eval_difference_kiki(board, teban_n):
    eval_diff_kyoku = Taikyoku(teban_n)
    eval_diff_kyoku.saki_yomitori_a(board)
    my_koma, opp_koma = conv_my_opp(board, teban_n)
    score = 0
    my_kiki = []
    opp_kiki = []
    for masu, my_km in my_koma.items():
        board_from_to = serch_kiki(masu, my_km, opp_koma,
                                   eval_diff_kyoku.aki, teban_n)
        my_kiki.extend(board_from_to)

    opp_teban_n = get_opp_teban_n(teban_n)
    for masu, opp_km in opp_koma.items():
        board_from_to = serch_kiki(masu, opp_km, my_koma,
                                   eval_diff_kyoku.aki, opp_teban_n)
        opp_kiki.extend(board_from_to)
    score = len(my_kiki) - len(opp_kiki)
    return score


def eval_hantei(board, teban_n):
    score = 0
    winner = None
    winner_c = hantei_catch(board, teban_n)
    winner_t = hantei_try(board, teban_n)
    if winner_c:
        winner = winner_c
    elif winner_t:
        winner = winner_t

    if winner:
        if teban_n == winner[1]:
            score += 500
        else:
            score -= 500
    return score


def eval_kata(board, teban_n):
    score = 0
    my_km, opp_km = conv_my_opp(board, teban_n)
    for ms, km in my_km.items():
        if km[0] == "e":
            if ms == "B2" and teban_n == "2":
                score += 5
                if board["A3"] == "g2" and board["C3"] == "g2":
                    score += 3
                if board["A3"] == "e2" and board["C3"] == "e2":
                    score += 3
                if board["A3"] == "c2" and board["C3"] == "c2":
                    score += 1
            if ms == "B3" and teban_n == "1":
                score += 5
                if board["A2"] == "g1" and board["C2"] == "g1":
                    score += 3
                if board["A2"] == "e1" and board["C2"] == "e1":
                    score += 3
                if board["A2"] == "c1" and board["C2"] == "c1":
                    score += 1

        if km[0] == "g":
            if teban_n == "1" and ms[1] == "4":
                score -= 4
            elif teban_n == "2" and ms[1] == "1":
                score -= 4

        if km[0] == "l":
            if ms[1] == "1" and teban_n == "2":
                score += 3
            elif ms[1] == "4" and teban_n == "1":
                score += 3
    return score


def conv_my_opp(board, teban_n):
    my_koma = {}
    opp_koma = {}
    conv = Taikyoku(teban_n)
    conv.saki_yomitori_p(board)
    if teban_n == "1":
        my_koma = conv.koma_p1
        opp_koma = conv.koma_p2
    elif teban_n == "2":
        my_koma = conv.koma_p2
        opp_koma = conv.koma_p1
    return my_koma, opp_koma


def get_opp_teban_n(teban_n):
    if teban_n == "1":
        opp_teban_n = "2"
    elif teban_n == "2":
        opp_teban_n = "1"
    return opp_teban_n


#@引数　辞書　board
#
#@返り値　リスト　banmen
#　　　　　リスト　koma_d
#　　　　　リスト　koma_e
def henkan_masu_to_list(board):
    koma_e = ["--", "--", "--", "--", "--", "--"]
    banmen = [["--", "--", "--"],
              ["--", "--", "--"],
              ["--", "--", "--"],
              ["--", "--", "--"]]
    koma_d = ["--", "--", "--", "--", "--", "--"]

    for masu, koma in board.items():
        if masu[0] == "D" or masu[0] == "E":
            if masu[0] == "D":
                okiba_d = int(masu[1]) - 1
                koma_d[okiba_d] = koma
            elif masu[0] == "E":
                okiba_e = int(masu[1]) - 1
                koma_e[okiba_e] = koma
        else:
            masu_in_list = masu_in_board_to_list(masu)
            for y in range(4):
                for x in range(3):
                    if str(y) + str(x) == masu_in_list:
                        banmen[y][x] = koma

    return banmen, koma_d, koma_e


#@引数　文字列　masu_in_board　　　２次元配列のインデックスに変換したい盤上のマス
#
#@返り値　文字列　masu_in_list　　　　　　
def masu_in_board_to_list(masu_in_board):
    tate = 9
    yoko = 9
    if masu_in_board[0] != "D" and masu_in_board[0] != "E":
        if masu_in_board[1] == "1":
            tate = 0
        elif masu_in_board[1] == "2":
            tate = 1
        elif masu_in_board[1] == "3":
            tate = 2
        elif masu_in_board[1] == "4":
            tate = 3

        if masu_in_board[0] == "A":
            yoko = 0
        elif masu_in_board[0] == "B":
            yoko = 1
        elif masu_in_board[0] == "C":
            yoko = 2

        masu_in_list =  str(tate) + str(yoko)
        return masu_in_list


#@引数　文字列　masu_in_list　　　　　リスト表示したマスのインデックス
#
#@返り値　文字列　masu_in_board　　　　　ボード表示したマスの場所
def masu_in_list_to_board(masu_in_list):
    masu_in_board_c = "S"
    masu_in_board_n = "n"
    tate = masu_in_list[0]
    yoko = masu_in_list[1]

    if tate == "0":
        masu_in_board_n = "1"
    elif tate == "1":
        masu_in_board_n = "2"
    elif tate == "2":
        masu_in_board_n = "3"
    elif tate == "3":
        masu_in_board_n = "4"

    if yoko == "0":
        masu_in_board_c = "A"
    elif yoko == "1":
        masu_in_board_c = "B"
    elif yoko == "2":
        masu_in_board_c = "C"

    masu_in_board = masu_in_board_c + masu_in_board_n
    return masu_in_board


BUFSIZE = 1024

serverName = "localhost"
serverPort = 4444

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((serverName, serverPort))

msg = s.recv(BUFSIZE).rstrip().decode()

msgbunkai = msg.split(" ")
a = msgbunkai[2]
my_teban = a[ :-1]
teban_n = my_teban[-1]
print("I am " + my_teban)

kyokumen_bf = Taikyoku(teban_n)
kyokumen_bf.yomitori(s, BUFSIZE)

while True:
    s.send(("turn\n").encode())
    time.sleep(0.1)

    msg_teban = s.recv(BUFSIZE).rstrip().decode()

    if msg_teban == my_teban:
        print("Myturn!")
        time.sleep(1.0)
        kyokumen = Taikyoku(teban_n)

        #相手の反則検知用に相手が動かした後の番を読み込む
        kyokumen.yomitori(s, BUFSIZE)

        #反則検知
        kyokumen.kenchi(kyokumen_bf.board, kyokumen.board)

        #勝敗の判定
        winner = kyokumen.hantei()
        if winner:
            print("winner is " + winner)
            break

        start = time.time()
        #着手
        kyokumen.chakushu(s)

        elapsed_time = time.time() - start
        print(elapsed_time)

        #勝敗の判定
        kyokumen.yomitori(s, BUFSIZE)
        winner = kyokumen.hantei()
        if winner:
            print("winner is " + winner)
            break

        #相手の反則検知用に相手が動かす前の番を読み込む
        kyokumen_bf.yomitori(s, BUFSIZE)
    else:
        print("Opponent turn!!")
        time.sleep(1.0)

print("Finish")

while True:
    line = input("")

    if re.match(r"^q\s*$", line):
        break

    s.send((line + "\n").encode())

    msg = s.recv(BUFSIZE)
    msg = msg.rstrip()

    print(msg.decode())

print("bye")

s.close()
