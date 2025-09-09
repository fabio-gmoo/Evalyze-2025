import { Routes } from '@angular/router';
import { HolaMundo } from './paginas/hola-mundo/hola-mundo';

export const routes: Routes = [
	{
		path: '',
		pathMatch: 'full',
		redirectTo: 'hola-mundo'
	},
	{
		path: 'hola-mundo',
		component: HolaMundo
	}
];
