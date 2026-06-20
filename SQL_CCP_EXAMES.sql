CREATE TABLE IF NOT EXISTS ccp_exames (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_paciente text NOT NULL,
    cpf text,
    cip text,
    celular text,
    exame text NOT NULL,
    convenio text,
    valor text,
    data_nascimento date,
    data_exame date,
    observacao text,
    status text NOT NULL DEFAULT 'entrada',
    criado_por uuid,
    criado_em timestamptz NOT NULL DEFAULT now(),
    atualizado_em timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ccp_exames_status ON ccp_exames(status);
CREATE INDEX IF NOT EXISTS idx_ccp_exames_criado_em ON ccp_exames(criado_em DESC);

CREATE TABLE IF NOT EXISTS ccp_tipos_exames (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome text NOT NULL,
    valor text,
    ativo boolean NOT NULL DEFAULT true,
    criado_em timestamptz NOT NULL DEFAULT now(),
    atualizado_em timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ccp_tipos_exames_nome ON ccp_tipos_exames(nome);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ccp_exames_status_check'
    ) THEN
        ALTER TABLE ccp_exames
        ADD CONSTRAINT ccp_exames_status_check
        CHECK (status IN ('entrada', 'aguardando_pagamento', 'pago', 'finalizado'));
    END IF;
END $$;
