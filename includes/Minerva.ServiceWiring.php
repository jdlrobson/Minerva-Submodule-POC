<?php

use MediaWiki\MediaWikiServices;

return [
	'Minerva.Config' => function ( MediaWikiServices $services ) {
		// FIXME: makeConfig should call with parameter minerva when a new repo is used
		return $services->getService( 'ConfigFactory' )
			->makeConfig( 'mobilefrontend' );
	}
];
