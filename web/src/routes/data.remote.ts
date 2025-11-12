import { query } from '$app/server';

export const getProjetos = query(() => {
	return [
		{
			idPl: 'PLL 001/25',
			idUrl: 140595,
			dataAbertura: new Date('2025-11-11'),
			tituloSimplificado:
				'Criação de auxílio financeiro para mães de pessoas com autismo, deficiência ou doença rara',
			autores: ['Grazi Oliveira (PSOL)']
		},
		{
			idPl: 'PLL 104/24',
			idUrl: 139985,
			dataAbertura: new Date('2025-9-11'),
			tituloSimplificado:
				'Garantia de acesso gratuito à água potável em estabelecimentos e eventos',
			autores: ['Roberto Robaina (PSOL)']
		},
		{
			idPl: 'PLL 001/25',
			idUrl: 140595,
			dataAbertura: new Date('2025-11-11'),
			tituloSimplificado:
				'Criação de auxílio financeiro para mães de pessoas com autismo, deficiência ou doença rara',
			autores: ['Grazi Oliveira (PSOL)']
		},
		{
			idPl: 'PLL 104/24',
			idUrl: 139985,
			dataAbertura: new Date('2025-9-11'),
			tituloSimplificado:
				'Garantia de acesso gratuito à água potável em estabelecimentos e eventos',
			autores: ['Roberto Robaina (PSOL)']
		}
	];
});
