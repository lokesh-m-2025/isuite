let
    Source = Web.Contents(S3BucketPath & "/input/sample-orders.csv"),
    ImportedCSV = Csv.Document(Source, [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    
    PromotedHeaders = Table.PromoteHeaders(ImportedCSV, [PromoteAllScalars=true]),
    
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"OrderDate", type date},
        {"ProductName", type text},
        {"Quantity", Int64.Type},
        {"UnitPrice", type number}
    }),
    
    AddedRevenueColumn = Table.AddColumn(ChangedTypes, "Revenue", each [Quantity] * [UnitPrice], type number),
    
    RemovedColumns = Table.RemoveColumns(AddedRevenueColumn, {"Quantity", "UnitPrice"}),
    
    AddedOrderID = Table.AddColumn(RemovedColumns, "OrderID", each Table.RowNumber(RemovedColumns), type text)

in
    AddedOrderID