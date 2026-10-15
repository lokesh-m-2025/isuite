let
    MinDate = Date.From(#date(2022, 1, 1)),
    MaxDate = Date.From(#date(2025, 12, 31)),
    DayCount = Duration.Days(MaxDate - MinDate) + 1,
    DateList = List.Dates(MinDate, DayCount, #duration(1, 0, 0, 0)),
    #"Converted to Table" = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    #"Changed Type" = Table.TransformColumnTypes(
        #"Converted to Table",
        {{"Date", type date}}
    ),
    #"Added Year" = Table.AddColumn(
        #"Changed Type",
        "Year",
        each Date.Year([Date]),
        type number
    ),
    #"Added Month" = Table.AddColumn(
        #"Added Year",
        "Month",
        each Date.Month([Date]),
        type number
    ),
    #"Added Month Name" = Table.AddColumn(
        #"Added Month",
        "Month Name",
        each Text.Proper(Date.ToText([Date], "MMMM")),
        type text
    ),
    #"Added Quarter" = Table.AddColumn(
        #"Added Month Name",
        "Quarter",
        each "Q" & Text.From(Number.RoundUp([Month] / 3)),
        type text
    ),
    #"Added Day of Week" = Table.AddColumn(
        #"Added Quarter",
        "Day of Week",
        each Text.Proper(Date.ToText([Date], "dddd")),
        type text
    )
in
    #"Added Day of Week"
