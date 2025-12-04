import { query } from '$app/server';

export const getProjeto = query(() => {
	return {
		id_externo: 140595,
		numero_processo: '01111/25',
		numero_projeto: '001/25',
		tipo: 'PLL',
		ementa:
			'118.00431/2025-14 ALTERA O PARAGRAFO UNICO DO ART. 1º DA LEI Nº 12.951, DE 7 DE JANEIRO DE 2022, QUE AUTORIZA O EXECUTIVO MUNICIPAL A CONTRATAR OPERACAO DE CREDITO COM O BANCO REGIONAL DE DESENVOLVIMENTO DO EXTREMO SUL (BRDE).',
		autores: [{ nome: 'GOVERNO MUNICIPAL' }],
		data_abertura: new Date('2025-09-08'),
		data_ultima_tramitacao: new Date('2025-10-17T16:21:00Z'),
		situacao: 'COM REDACAO FINAL',
		situacao_plenaria: 'APROVADO',
		status: 'Aprovado',
		localizacao_atual: 'SECAO DE COMISSOES',
		analise_ia: {
			modelo: 'gemini-3-pro-preview',
			titulo: 'Ampliação de obras de drenagem e pavimentação no Loteamento Albion',
			resumo:
				'Autoriza o uso de recursos do financiamento do Túnel Verde para realizar obras de drenagem e pavimentação também no Loteamento Albion.',
			mudancas: [
				{
					texto:
						'O dinheiro emprestado pelo banco, antes restrito ao Túnel Verde, agora poderá ser usado também para pavimentar ruas e instalar redes de esgoto pluvial no Loteamento Albion e em outras obras de drenagem ligadas ao projeto.',
					fontes: [
						'abrangendo, além da execução de canal, diques e casas de bombas do Projeto Túnel Verde, obras complementares de microdrenagem e pavimentação diretamente vinculadas ao referido projeto, inclusive nas áreas de contribuição do Loteamento Albion'
					]
				},
				{
					texto:
						'A Prefeitura não pegará mais dinheiro emprestado nem criará novas dívidas; a lei apenas permite usar o mesmo valor já aprovado para fazer mais obras.',
					fontes: [
						'A alteração proposta não implica aumento no valor da operação de crédito nem gera novas obrigações financeiras para o Município.'
					]
				}
			],
			justificativas: [
				{
					texto:
						'O projeto original do Túnel Verde ficou mais barato que o previsto, sobrando margem no orçamento para realizar outras melhorias.',
					fontes: [
						'foi possível uma redução nos orçamentos relativos aos canais e às redes de microdrenagem, os quais inicialmente correspondiam a aproximadamente 80% (oitenta por cento) do custo total do investimento.'
					]
				},
				{
					texto:
						'A Prefeitura identificou a oportunidade de resolver problemas de drenagem no Loteamento Albion, que joga água diretamente no canal do Túnel Verde.',
					fontes: [
						'identificou-se a oportunidade de ampliar o escopo para incluir a implantação de redes de microdrenagem e pavimentação, seguindo os mesmos parâmetros adotados na proposta do Loteamento do Túnel Verde, na área do Loteamento Albion que contribui diretamente para o Canal do Túnel Verde.'
					]
				},
				{
					texto:
						'Os bancos financiadores já aceitaram a inclusão dessas novas obras, mas exigem que a lei municipal seja atualizada para liberar o uso do dinheiro.',
					fontes: [
						'confirmaram a elegibilidade da ampliação do escopo do projeto junto ao Banco Internacional para Reconstrução e Desenvolvimento (BIRD). No entanto, essa aprovação está condicionada à flexibilização da autorização legislativa'
					]
				}
			],
			classificacao: [
				{
					categoria: 'Urbanismo e infraestrutura',
					fontes: [
						'investimentos em saneamento na modalidade manejo de águas pluviais',
						'obras complementares de microdrenagem e pavimentação'
					]
				},
				{
					categoria: 'Economia e finanças',
					fontes: [
						'contratar operação de crédito junto ao Banco Regional de Desenvolvimento do Extremo Sul (BRDE)',
						'não implica aumento no valor da operação de crédito'
					]
				}
			]
		},
		anexos: [
			{
				titulo: 'Projeto',
				url: 'https://www.camarapoa.rs.gov.br/draco/processos/141613/PLE_053-25.pdf'
			},
			{
				titulo: 'Parecer prévio n° 1042-2025',
				url: 'https://www.camarapoa.rs.gov.br/draco/processos/141613/Parecer_pr%C3%A9vio_n%C2%B0_1042-2025.pdf'
			},
			{
				titulo: 'Parecer Conjunto nº 132/25 - CCJ/CEFOR/CUTHAB/COSMAM - AO PROJETO',
				url: 'https://www.camarapoa.rs.gov.br/draco/processos/141613/132-25A_-_29SET_-_PARECER_CONJUNTO_-_PROC._1018-25_-_PLE_053_-_IC.pdf'
			},
			{
				titulo: 'Redação Final',
				url: 'https://www.camarapoa.rs.gov.br/draco/processos/141613/RF_-_09OUT2025_-_PROC._1018-25_-_PLE_053.pdf'
			},
			{
				titulo: 'Lei nº 14.340/25',
				url: 'https://www.camarapoa.rs.gov.br/draco/processos/141613/Lei_14340.pdf'
			}
		],
		votacoes: [
			{
				data: new Date('2025-10-01'),
				titulo: 'PLE 053/25 - PROC. 1018/25',
				votos_sim: null,
				votos_nao: null,
				abstencoes: null,
				resultado: 'Aprovado',
				detalhes_url: 'https://votacoes.camarapoa.rs.gov.br/votacoes/17628'
			}
		],
		tramitacoes: [
			{
				setor: 'SECAO DE COMISSOES',
				data_chegada: new Date('2025-10-17'),
				data_saida: new Date('2025-10-01'),
				situacao: 'COM REDACAO FINAL'
			},
			{
				setor: 'SECAO DE COMISSOES',
				data_chegada: new Date('2025-10-01'),
				data_saida: new Date('2025-10-17'),
				situacao: 'COM REDACAO FINAL'
			}
		]
	};
});
