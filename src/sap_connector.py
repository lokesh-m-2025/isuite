import logging
from pyspark.sql import SparkSession, DataFrame
from src.config import PipelineConfig

logger = logging.getLogger(__name__)

class SAPExtractor:
    """Extracts SAP Sales Data via Spark JDBC pushdown."""
    def __init__(self, spark: SparkSession, config: PipelineConfig):
        self.spark = spark
        self.config = config

    def extract_sales_orders(self, watermark_timestamp: str) -> DataFrame:
        """Extracts VBAK (Sales Header) joined with VBAP (Sales Item) changed after watermark."""
        jdbc_url = self.config.sap_jdbc_url
        props = self.config.get_spark_jdbc_properties()
        
        header_tbl = self.config.sap_table_header
        item_tbl = self.config.sap_table_item
        
        pushdown_query = f"""
            (SELECT 
                h.VBELN AS sales_doc_num,
                h.ERDAT AS create_date,
                h.AEDAT AS update_date,
                h.ERNAM AS created_by,
                h.AUDAT AS doc_date,
                h.VBTYP AS doc_type,
                h.NETWR AS header_net_value,
                h.WAERK AS doc_currency,
                h.VKORG AS sales_org,
                h.VTWEG AS dist_channel,
                h.SPART AS division,
                i.POSNR AS item_num,
                i.MATNR AS material_num,
                i.MATKL AS material_group,
                i.KWMENG AS order_qty,
                i.VRKME AS sales_unit,
                i.NETWR AS item_net_value,
                i.WERKS AS plant
            FROM {header_tbl} h
            INNER JOIN {item_tbl} i ON h.VBELN = i.VBELN
            WHERE h.AEDAT >= '{watermark_timestamp}' OR h.ERDAT >= '{watermark_timestamp}') AS sap_sales_query
        """
        
        logger.info(f"Executing SAP Extraction pushdown query for watermark: {watermark_timestamp}")
        return self.spark.read.jdbc(
            url=jdbc_url,
            table=pushdown_query,
            properties=props
        )
