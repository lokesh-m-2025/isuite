let
    Source = Csv.Document(
        Web.Contents(
            "s3://ignitho-development-bucket/input/sample-orders.csv"
        ),
        [Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(
        #"Promoted Headers",
        {
            {"order_date", type date},
            {"product_name", type text},
            {"amount", type number}
        }
    ),
    #"Removed Blank Rows" = Table.SelectRows(
        #"Changed Type",
        each [order_date] <> null and [product_name] <> "" and [amount] <> null
    ),
    #"Trimmed Text" = Table.TransformColumns(
        #"Removed Blank Rows",
        {{"product_name", Text.Trim}}
    )
in
    #"Trimmed Text"
