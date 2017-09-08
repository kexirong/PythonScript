def list_index(List,sub_ele,Index=[],a=0): #Index=None
    Index=Index[:]
    for i in List:
        if  isinstance(i,list):
            Index.append(a)
            x=list_index(i,sub_ele,Index,a=0)
            if x: return x
            Index.pop()
        elif sub_ele == i:
            Index.append(a)
            return Index
        #else:pass
        a+=1


if __name__=="__main__":
    list1=["a","b","c","d","e","f","g","h","i","j","k"]
    list2=[["a"],["b"],"c",[["d"],["e",["f"],["g"],[["h"],[["i"],[["j",["k"]]]]]]]]
    for ele in list1:
        print(list_index(list2,ele))
'''        
#求任意结构list 的 某元素 的index,只找一次      
$ python  ListiIndex.py
[0, 0]
[1, 0]
[2]
[3, 0, 0]
[3, 1, 0]
[3, 1, 1, 0]
[3, 1, 2, 0]
[3, 1, 3, 0, 0]
[3, 1, 3, 1, 0, 0]
[3, 1, 3, 1, 1, 0, 0]
[3, 1, 3, 1, 1, 0, 1, 0]
'''
