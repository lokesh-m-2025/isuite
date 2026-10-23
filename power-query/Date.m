let
    Orders = #"Orders",
    
    MinDate = List.Min(Orders[OrderDate]),
    MaxDate = List.Max(Orders[OrderDate]),
    
    DateRange = {MinDate..MaxDate},
    
    ConvertedToTable = Table.FromList(DateRange, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    
    RenamedColumn = Table.RenameColumns(ConvertedToTable, {{"Column1", "Date"}}),
    
    ChangedType = Table.TransformColumnTypes(RenamedColumn, {{"Date", type date}}),
    
    AddedYear = Table.AddColumn(ChangedType, "Year", each Date.Year([Date]), Int64.Type),
    AddedQuarter = Table.AddColumn(AddedYear, "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    AddedMonth = Table.AddColumn(AddedQuarter, "Month", each Date.Month([Date]), Int64.Type),
    AddedMonthName = Table.AddColumn(AddedMonth, "MonthName", each Text.Proper(Date.ToText([Date], "MMMM")), type text),
    AddedWeek = Table.AddColumn(AddedMonthName, "WeekOfYear", each Date.WeekOfYear([Date], Day.Monday), Int64.Type),
    AddedDayOfWeek = Table.AddColumn(AddedWeek, "DayOfWeek", each Text.Proper(Date.ToText([Date], "dddd")), type text),
    
    YearMonth = Table.AddColumn(AddedDayOfWeek, "YearMonth", each Text.From([Year]) & "-" & Text.PadStart(Text.From([Month]), 2, "0"), type text),
    
    FinalTable = Table.ReorderColumns(YearMonth, {"Date", "Year", "Quarter", "Month", "MonthName", "WeekOfYear", "DayOfWeek", "YearMonth"})

in
    FinalTable