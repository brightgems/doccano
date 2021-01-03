# code: utf-8

class CorpusProcess(object):
    def read_corpus_from_file(self, file_path):
        """读取语料"""
        f = open(file_path, 'r',encoding='utf-8')
        lines = f.readlines()
        f.close()
        return lines

    def q_to_b(self,q_str):
        """全角转半角"""
        b_str = ""
        for uchar in q_str:
            inside_code = ord(uchar)
            if inside_code == 12288:  # 全角空格直接转换
                inside_code = 32
            elif 65374 >= inside_code >= 65281:  # 全角字符（除空格）根据关系转化
                inside_code -= 65248
            b_str += chr(inside_code)
        return b_str
    
    def b_to_q(self,b_str):
        """半角转全角"""
        q_str = ""
        for uchar in b_str:
            inside_code = ord(uchar)
            if inside_code == 32:  # 半角空格直接转化
                inside_code = 12288
            elif 126 >= inside_code >= 32:  # 半角字符（除空格）根据关系转化
                inside_code += 65248
            q_str += chr(inside_code)
        return q_str
    
    def pre_process(self, train_corpus_path):
        """语料预处理 """
        lines = self.read_corpus_from_file(train_corpus_path)
        new_lines = []
        for line in lines:
            words = self.q_to_b(line.strip()).split(u'  ')
            new_lines.append('  '.join(pro_words[1:]))
        return lines
    