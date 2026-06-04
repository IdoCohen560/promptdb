"""Labeled gold set for execution-accuracy evals (Chinook).

Each item: question, gold SQL, and a difficulty bucket for failure-mode analysis.
Spider dev subset plugs in here later behind the same interface.
"""

GOLD: list[dict] = [
    {"q": "How many customers are there?",
     "sql": "SELECT COUNT(*) FROM Customer", "diff": "simple"},
    {"q": "List the names of all genres.",
     "sql": "SELECT Name FROM Genre", "diff": "simple"},
    {"q": "How many customers are from Brazil?",
     "sql": "SELECT COUNT(*) FROM Customer WHERE Country = 'Brazil'", "diff": "filter"},
    {"q": "How many distinct billing countries appear in invoices?",
     "sql": "SELECT COUNT(DISTINCT BillingCountry) FROM Invoice", "diff": "filter"},
    {"q": "What is the total revenue across all invoices?",
     "sql": "SELECT ROUND(SUM(Total), 2) FROM Invoice", "diff": "aggregation"},
    {"q": "What is the longest track length in milliseconds?",
     "sql": "SELECT MAX(Milliseconds) FROM Track", "diff": "aggregation"},
    {"q": "Which 5 artists earned the most revenue?",
     "sql": ("SELECT ar.Name, ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS rev "
             "FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId "
             "JOIN Track t ON al.AlbumId = t.AlbumId "
             "JOIN InvoiceLine il ON t.TrackId = il.TrackId "
             "GROUP BY ar.ArtistId, ar.Name ORDER BY rev DESC LIMIT 5"),
     "diff": "join"},
    {"q": "How many tracks does each media type have?",
     "sql": ("SELECT mt.Name, COUNT(*) AS c FROM MediaType mt "
             "JOIN Track t ON mt.MediaTypeId = t.MediaTypeId "
             "GROUP BY mt.MediaTypeId, mt.Name"), "diff": "join"},
    {"q": "Which countries have more than 5 customers?",
     "sql": "SELECT Country, COUNT(*) AS c FROM Customer GROUP BY Country HAVING c > 5",
     "diff": "group_having"},
    {"q": "What are the top 3 genres by number of tracks?",
     "sql": ("SELECT g.Name, COUNT(*) AS c FROM Genre g JOIN Track t ON g.GenreId = t.GenreId "
             "GROUP BY g.GenreId ORDER BY c DESC LIMIT 3"), "diff": "group_having"},
    {"q": "Which genre has the most tracks? Return only the genre name.",
     "sql": ("SELECT g.Name FROM Genre g JOIN Track t ON g.GenreId = t.GenreId "
             "GROUP BY g.GenreId ORDER BY COUNT(*) DESC LIMIT 1"), "diff": "nested"},
    {"q": "List the first and last names of customers who have spent more than 45 dollars in total.",
     "sql": ("SELECT c.FirstName, c.LastName "
             "FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId "
             "GROUP BY c.CustomerId HAVING SUM(i.Total) > 45"), "diff": "nested"},
]
