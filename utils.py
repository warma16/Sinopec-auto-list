import numpy as np
import pandas as pd
import re
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DocumentClusterer')

# ===== 1. 增强型动态表头处理器 =====
class RobustHeaderParser:
    def __init__(self):
        # 表头映射（支持中英文变体）
        self.header_map = {
            "purchase_order": ["PURCHASE ORDER", "采购订单", "订单号", "PO", "PO编号"],
            "tr_number": ["TR NUMBER", "技术请求号", "TR号", "TR NUM", "TR编号"],
            "doc_title": ["DOCUMENT TITLE", "文件标题", "文档名称", "TITLE", "文件描述"],
            "critical": ["CRITICAL-CRIT", "紧急程度", "关键标记", "CRIT", "Y/N", "重要程度"],
            "responsible": ["责任人", "负责人", "RESPONSIBLE", "负责人", "处理人", "对接人"],
            "status": ["状态", "STATUS", "当前状态", "审批状态", "流程状态"],
            "days": ["TOTAL DAYS", "超期天数", "DAYS", "流转天数", "处理时长"]
        }
        
        # 设备ID识别模式
        self.equipment_patterns = [
            r"(?:ITEM|设备|设备号|EQUIP)\s*[:：]\s*([A-Z0-9]+-[A-Z0-9-]+)",
            r"(?:FOR|针对)\s+([A-Z0-9]+-[A-Z0-9-]+)",
            r"\b([A-Z]{2,}-\d+-\d{4}[A-Z]?)\b"
        ]
        
        # 文档类型识别模式
        self.doc_type_patterns = {
            "技术参数表": ["DATA SHEET", "规格书", "技术参数", "DATASHEET"],
            "操作流程": ["PROCEDURE", "规程", "流程", "操作指导"],
            "工程图纸": ["DRAWING", "图纸", "图样", "示意图"],
            "计算书": ["CALCULATION", "计算书", "核算", "验算"],
            "报告": ["REPORT", "报告", "报表", "汇总"],
            "清单": ["LIST", "清单", "列表", "目录"]
        }
    
    def parse_headers(self, header_line):
        """动态识别表头字段位置"""
        try:
            # 分割可能的表头字段
            possible_headers = re.split(r'\t+|\s{3,}', header_line.strip())
            
            # 匹配已知表头
            matched_headers = {}
            for idx, text in enumerate(possible_headers):
                clean_text = re.sub(r'\W+', '', text.strip().upper())
                for field, aliases in self.header_map.items():
                    for alias in aliases:
                        clean_alias = re.sub(r'\W+', '', alias.upper())
                        if clean_alias and clean_alias in clean_text:
                            if field not in matched_headers:  # 避免重复匹配
                                matched_headers[field] = idx
                            break
            
            return matched_headers
        except Exception as e:
            logger.error(f"表头解析失败: {str(e)}")
            return {}
    
    def extract_equipment_id(self, text):
        """从文本中提取设备ID"""
        try:
            for pattern in self.equipment_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return ""
        except:
            return ""
    
    def extract_doc_type(self, text):
        """识别文档类型"""
        try:
            for doc_type, keywords in self.doc_type_patterns.items():
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        return doc_type
            return "其他文档"
        except:
            return "其他文档"
    
    def parse_row(self, line, header_mapping):
        """解析单行数据"""
        try:
            # 安全分割列（考虑制表符和多个空格）
            columns = re.split(r'\t+| {2,}', line.strip())
            row = {}
            
            # 提取已知字段
            for field, idx in header_mapping.items():
                if idx < len(columns):
                    row[field] = columns[idx].strip()
            
            # 组合原始文本
            full_text = " ".join(columns)
            
            # 智能提取关键信息
            equipment_id = self.extract_equipment_id(full_text)
            doc_type = self.extract_doc_type(full_text)
            
            # 提取紧急程度
            critical = "N"
            if 'critical' in row:
                critical = "Y" if "Y" in row['critical'].upper() else "N"
            else:
                if "紧急" in full_text or "CRITICAL" in full_text or "!!!" in full_text:
                    critical = "Y"
            
            # 提取状态
            status = row.get('status', '')
            if not status:
                if "审批" in full_text or "APPROV" in full_text:
                    status = "审批中"
                elif "超期" in full_text or "DELAY" in full_text:
                    status = "超期"
                elif "完成" in full_text or "DONE" in full_text:
                    status = "已完成"
            
            # 提取负责人
            responsible = row.get('responsible', '')
            if not responsible:
                # 中文姓名识别
                name_match = re.search(r"[\u4e00-\u9fa5]{2,3}", full_text)
                if name_match:
                    responsible = name_match.group(0)
            
            return {
                "equipment_id": equipment_id,
                "doc_type": doc_type,
                "critical": critical,
                "status": status,
                "responsible": responsible,
                "full_text": full_text,  # 用于聚类
                "raw_line": line  # 保留原始行
            }
        except Exception as e:
            logger.error(f"行解析失败: {line[:50]}... | 错误: {str(e)}")
            return None

# ===== 2. 文档预处理器（空数据保护）=====
def robust_preprocess(content):
    """鲁棒的文档预处理（带空数据保护）"""
    parser = RobustHeaderParser()
    
    # 空内容处理
    if not content.strip():
        logger.warning("输入内容为空")
        return []
    
    # 寻找可能的表头
    lines = content.split('\n')
    if len(lines) < 3:  # 文件过短
        logger.warning("文档行数过少，可能不是完整文档")
        return []
    
    header_candidates = []
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in ["ORDER", "TR", "TITLE", "责任人", "状态"]):
            header_candidates.append((i, line))
    
    # 选择最佳表头行（包含最多关键词）
    best_header = None
    best_score = 0
    for i, line in header_candidates:
        score = sum(1 for field in parser.header_map.values() 
                   for alias in field if alias in line)
        if score > best_score:
            best_score = score
            best_header = (i, line)
    
    # 解析表头
    header_mapping = {}
    if best_header:
        _, header_line = best_header
        header_mapping = parser.parse_headers(header_line)
    
    # 解析数据行
    parsed_data = []
    start_index = best_header[0] + 1 if best_header else 0
    
    for line in lines[start_index:]:
        if not line.strip() or len(line.strip()) < 10:  # 跳过空行和短行
            continue
            
        # 跳过表头分隔线
        if re.match(r'^[-=]+$', line.strip()):
            continue
            
        # 跳过纯数字行（可能是页码）
        if re.match(r'^\d+$', line.strip()):
            continue
            
        parsed = parser.parse_row(line, header_mapping)
        if parsed is not None:  # 过滤解析失败的行
            # 只有包含关键信息才添加
            if parsed['equipment_id'] or parsed['doc_type'] != '其他文档':
                parsed_data.append(parsed)
    
    return parsed_data

# ===== 3. 增强型聚类引擎（空集群保护）=====
class DocumentClusterer:
    def __init__(self, similarity_threshold=0.72):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            min_df=1,  # 降低阈值防止空数据
            max_features=5000  # 限制特征数量
        )
    
    def cluster_documents(self, documents):
        """对文档进行语义聚类（带多重空集群保护）"""
        # 空输入处理
        if not documents:
            logger.warning("聚类输入为空")
            return []
        
        # 小数据集直接返回不聚类
        if len(documents) <= 3:
            logger.info("数据集过小，跳过聚类")
            return [self._create_single_doc_cluster(doc) for doc in documents]
        
        # 准备聚类文本
        texts = [doc['full_text'] for doc in documents]
        
        try:
            # 向量化
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # 空矩阵处理
            if tfidf_matrix.shape[0] == 0 or tfidf_matrix.shape[1] == 0:
                logger.warning("TF-IDF矩阵为空，使用回退策略")
                return self._fallback_clustering(documents)
            
            # 计算余弦相似度
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # 聚类文档
            clusters = []
            visited = set()
            
            for idx in range(len(documents)):
                if idx in visited:
                    continue
                    
                # 查找相似文档
                similar_indices = np.where(cosine_sim[idx] > self.similarity_threshold)[0]
                cluster_docs = [documents[i] for i in similar_indices]
                
                # 空集群保护
                if not cluster_docs:
                    logger.warning(f"集群{idx}为空，跳过")
                    continue
                
                # 生成集群摘要
                cluster_summary = self._generate_cluster_summary(cluster_docs)
                if cluster_summary:  # 确保摘要有效
                    clusters.append(cluster_summary)
                visited.update(similar_indices)
            
            # 处理未聚类文档
            unclustered = [i for i in range(len(documents)) if i not in visited]
            for idx in unclustered:
                clusters.append(self._create_single_doc_cluster(documents[idx]))
            
            return clusters
        except Exception as e:
            logger.error(f"聚类失败: {str(e)}，使用回退策略")
            return self._fallback_clustering(documents)
    
    def _create_single_doc_cluster(self, doc):
        """创建单文档集群"""
        return {
            "summary": doc['full_text'][:100] + ("..." if len(doc['full_text']) > 100 else ""),
            "count": 1,
            "critical": doc['critical'],
            "responsible": doc['responsible'],
            "status": doc.get('status', ''),
            "items": [doc]
        }
    
    def _generate_cluster_summary(self, cluster_docs):
        """生成集群摘要（带空输入保护）"""
        # 空输入保护
        if not cluster_docs:
            logger.warning("尝试生成空集群摘要")
            return None
        
        try:
            # 提取公共设备ID（如果存在）
            equipment_ids = defaultdict(int)
            for doc in cluster_docs:
                if doc['equipment_id']:
                    equipment_ids[doc['equipment_id']] += 1
            
            # 按设备分组生成摘要
            if equipment_ids:
                summaries = []
                for equip_id, count in equipment_ids.items():
                    # 获取该设备的关键文档
                    equip_docs = [doc for doc in cluster_docs if doc['equipment_id'] == equip_id]
                    doc_types = defaultdict(int)
                    for doc in equip_docs:
                        doc_types[doc['doc_type']] += 1
                    
                    type_desc = "、".join([f"{c}份{t}" for t, c in doc_types.items()])
                    critical_count = sum(1 for doc in equip_docs if doc['critical'] == 'Y')
                    
                    summaries.append({
                        "summary": f"{count}份{equip_id}相关文件({type_desc})",
                        "equipment_id": equip_id,
                        "count": count,
                        "critical_count": critical_count,
                        "representative": equip_docs[0]['full_text'][:100] + ("..." if len(equip_docs[0]['full_text']) > 100 else ""),
                        "responsible": equip_docs[0]['responsible'] if equip_docs else "",
                        "items": equip_docs
                    })
                
                # 如果只有一个设备组，直接返回
                if len(summaries) == 1:
                    return summaries[0]
                
                # 多个设备组合并
                total_count = len(cluster_docs)
                equipment_list = ", ".join(equipment_ids.keys())
                return {
                    "summary": f"{total_count}份相关文件（设备: {equipment_list}）",
                    "count": total_count,
                    "sub_clusters": summaries,
                    "items": cluster_docs
                }
            
            # 按文档类型分组
            doc_types = defaultdict(int)
            for doc in cluster_docs:
                doc_types[doc['doc_type']] += 1
            
            type_desc = "、".join([f"{c}份{t}" for t, c in doc_types.items()])
            critical_count = sum(1 for doc in cluster_docs if doc['critical'] == 'Y')
            
            return {
                "summary": f"{len(cluster_docs)}份相关文件({type_desc})",
                "count": len(cluster_docs),
                "critical_count": critical_count,
                "representative": cluster_docs[0]['full_text'][:100] + ("..." if len(cluster_docs[0]['full_text']) > 100 else ""),
                "responsible": cluster_docs[0]['responsible'],
                "items": cluster_docs
            }
        except Exception as e:
            logger.error(f"生成集群摘要失败: {str(e)}")
            # 回退到简单摘要
            return {
                "summary": f"{len(cluster_docs)}份相关文件",
                "count": len(cluster_docs),
                "items": cluster_docs
            }
    
    def _fallback_clustering(self, documents):
        """回退聚类策略（当TF-IDF失败时）"""
        logger.info("使用回退聚类策略")
        # 简单按设备ID分组
        clusters = defaultdict(list)
        for doc in documents:
            key = doc['equipment_id'] or doc['doc_type'] or "其他"
            clusters[key].append(doc)
        
        result = []
        for key, docs in clusters.items():
            if not docs:  # 空集群保护
                continue
                
            critical_count = sum(1 for doc in docs if doc['critical'] == 'Y')
            result.append({
                "summary": f"{len(docs)}份{key}相关文件",
                "count": len(docs),
                "critical_count": critical_count,
                "items": docs
            })
        
        return result

# ===== 4. 聚类后处理器（空集群保护）=====
class ClusterPostProcessor:
    def __init__(self):
        self.now = datetime.now()
    
    def generate_summary(self, clusters):
        """生成压缩摘要报告（带空集群保护）"""
        # 空输入处理
        if not clusters:
            return "⚠️ 未生成任何集群，请检查输入数据"
        
        try:
            total_files = sum(c['count'] for c in clusters)
            critical_files = sum(c.get('critical_count', 0) for c in clusters)
            
            # 按负责人统计
            responsible_stats = defaultdict(int)
            for cluster in clusters:
                if 'sub_clusters' in cluster:
                    for sub in cluster['sub_clusters']:
                        self._count_responsible(sub, responsible_stats)
                else:
                    self._count_responsible(cluster, responsible_stats)
            
            # 生成报告
            report = f"文档压缩报告 ({self.now.strftime('%Y-%m-%d')})\n"
            report += "=" * 50 + "\n"
            report += f"• 原始文件数: {total_files}\n"
            report += f"• 压缩后集群: {len(clusters)}\n"
            report += f"• 紧急文件数: {critical_files}\n\n"
            
            if responsible_stats:
                report += "【负责人统计】\n"
                for person, count in sorted(responsible_stats.items(), key=lambda x: x[1], reverse=True):
                    report += f"  - {person}: {count}份文件\n"
            
            report += "\n【关键集群摘要】\n"
            for i, cluster in enumerate(clusters[:5]):  # 显示前5个集群
                report += f"{i+1}. {cluster['summary']}"
                if cluster.get('critical_count', 0) > 0:
                    report += f" [含{cluster['critical_count']}份紧急]"
                report += "\n"
            
            # 添加警告信息
            if len(clusters) > 20:
                report += f"\n⚠️ 注意: 共生成{len(clusters)}个集群，可能聚类效果不佳"
            
            return report
        except Exception as e:
            logger.error(f"生成摘要失败: {str(e)}")
            return f"报告生成失败: {str(e)}"
    
    def _count_responsible(self, cluster, stats):
        """统计负责人（空值保护）"""
        for item in cluster.get('items', []):
            if item and item.get('responsible'):
                stats[item['responsible']] += 1
    
    def save_clusters(self, clusters, filename):
        """保存聚类结果（空集群保护）"""
        if not clusters:
            return "⚠️ 无集群数据可保存"
        
        try:
            # 简化结构以方便存储
            simplified = []
            for cluster in clusters:
                simple_cluster = {
                    "summary": cluster.get("summary", "无摘要"),
                    "count": cluster.get("count", 0),
                    "critical_count": cluster.get("critical_count", 0)
                }
                
                # 添加代表项
                if "representative" in cluster:
                    simple_cluster["representative"] = cluster["representative"]
                
                # 处理子集群
                if "sub_clusters" in cluster:
                    simple_cluster["sub_clusters"] = [
                        {"summary": sc["summary"], "count": sc["count"]} 
                        for sc in cluster["sub_clusters"]
                    ]
                
                simplified.append(simple_cluster)
            
            # 保存为JSON
            df = pd.DataFrame(simplified)
            if not df.empty:
                df.to_json(filename, orient="records", force_ascii=False)
                return f"结果已保存至 {filename}"
            return "⚠️ 无有效数据可保存"
        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")
            return f"保存失败: {str(e)}"

# ===== 5. 主控制器（全面错误处理）=====
def process_industrial_document(content, output_prefix="document_clusters"):
    """处理工业文档的完整流程（带全面错误处理）"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_prefix}_{timestamp}.json"
        
        # 1. 文档预处理
        logger.info("正在解析文档结构...")
        parsed_data = robust_preprocess(content)
        logger.info(f"成功解析 {len(parsed_data)} 行数据")
        
        # 空数据保护
        if not parsed_data:
            return {
                "status": "error",
                "message": "未解析出有效数据，请检查文档格式",
                "summary": "无有效数据可处理"
            }
        
        # 2. 语义聚类
        logger.info("正在进行语义聚类...")
        clusterer = DocumentClusterer(similarity_threshold=0.7)
        clusters = clusterer.cluster_documents(parsed_data)
        logger.info(f"生成 {len(clusters)} 个语义集群")
        
        # 3. 生成摘要
        logger.info("生成摘要报告...")
        post_processor = ClusterPostProcessor()
        summary = post_processor.generate_summary(clusters)
        
        # 4. 保存结果
        #save_result = post_processor.save_clusters(clusters, output_file)
        
        return {
            "status": "success",
            "summary": summary,
            "cluster_count": len(clusters),
            "original_count": len(parsed_data),
            "compression_rate": 1 - len(clusters)/len(parsed_data) if parsed_data else 0,
            "save_path": output_file,
            "clusters_sample": clusters[:3] if clusters else []
        }
    except Exception as e:
        logger.exception("文档处理流程失败")
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}",
            "summary": "文档处理过程中发生错误"
        }

