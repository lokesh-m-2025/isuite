let
    Orders = #"Orders",
    
    UniqueProducts = Table.Distinct(Orders, {"ProductName"}),
    
    AddedProductID = Table.AddColumn(UniqueProducts, "ProductID", each Text.From(Table.RowNumber(UniqueProducts)), type text),
    
    ReorderedColumns = Table.ReorderColumns(AddedProductID, {"ProductID", "ProductName"}),
    
    RemovedRevenue = Table.RemoveColumns(ReorderedColumns, {"Revenue", "OrderID", "OrderDate"})

in
    RemovedRevenue