ALTER TABLE convenios
ADD COLUMN IF NOT EXISTS ordem INTEGER;

UPDATE convenios
SET ordem = ordem_temp
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY criado_em DESC) AS ordem_temp
    FROM convenios
) x
WHERE convenios.id = x.id
AND convenios.ordem IS NULL;
